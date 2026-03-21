package main

import (
	"crypto/tls"
	"crypto/x509"
	"io"
	"log"
	"net/http"
	"net/http/httputil"
	"net/url"
	"os"
	"strings"
)

func reverseProxy(target string) *httputil.ReverseProxy {
	u, err := url.Parse(target)
	if err != nil {
		panic(err)
	}
	return httputil.NewSingleHostReverseProxy(u)
}

func requireRole(allowed ...string) func(http.Handler) http.Handler {
	set := map[string]bool{}
	for _, r := range allowed {
		set[r] = true
	}
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			role := strings.ToLower(r.Header.Get("X-Role"))
			if role == "" || !set[role] {
				w.WriteHeader(http.StatusForbidden)
				_, _ = io.WriteString(w, `{"error":"insufficient_role"}`)
				return
			}
			next.ServeHTTP(w, r)
		})
	}
}

func main() {
	billingURL := env("BILLING_URL", "http://billing:8001")
	inventoryURL := env("INVENTORY_URL", "http://inventory:8002")
	syncURL := env("SYNC_URL", "http://sync:8003")
	port := env("PORT", "8080")

	billingProxy := reverseProxy(billingURL)
	inventoryProxy := reverseProxy(inventoryURL)
	syncProxy := reverseProxy(syncURL)

	mux := http.NewServeMux()
	mux.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		_, _ = io.WriteString(w, `{"status":"ok"}`)
	})

	mux.Handle("/orders", requireRole("manager", "cashier")(billingProxy))
	mux.Handle("/orders/", requireRole("manager", "cashier")(billingProxy))
	mux.Handle("/bills", requireRole("manager", "cashier")(billingProxy))
	mux.Handle("/bills/", requireRole("manager", "cashier")(billingProxy))
	mux.Handle("/kds/", requireRole("manager", "kitchen_staff", "cashier")(billingProxy))
	mux.Handle("/menu/", requireRole("manager", "cashier")(billingProxy))
	mux.Handle("/reports/", requireRole("manager", "cashier")(billingProxy))
	mux.Handle("/ledger/", requireRole("manager")(billingProxy))

	mux.Handle("/inventory/", requireRole("manager")(inventoryProxy))
	mux.Handle("/sync/", requireRole("manager", "cashier", "kitchen_staff")(syncProxy))

	log.Printf("gateway listening on :%s", port)
	if err := listen(mux, port); err != nil {
		log.Fatal(err)
	}
}

func listen(handler http.Handler, port string) error {
	certFile := os.Getenv("TLS_CERT_FILE")
	keyFile := os.Getenv("TLS_KEY_FILE")
	caFile := os.Getenv("TLS_CA_FILE")
	if certFile == "" || keyFile == "" || caFile == "" {
		return http.ListenAndServe(":"+port, handler)
	}

	caPEM, err := os.ReadFile(caFile)
	if err != nil {
		return err
	}
	caPool := x509.NewCertPool()
	if !caPool.AppendCertsFromPEM(caPEM) {
		return io.ErrUnexpectedEOF
	}

	s := &http.Server{
		Addr:    ":" + port,
		Handler: handler,
		TLSConfig: &tls.Config{
			ClientAuth: tls.RequireAndVerifyClientCert,
			ClientCAs:  caPool,
			MinVersion: tls.VersionTLS13,
		},
	}
	return s.ListenAndServeTLS(certFile, keyFile)
}

func env(k, d string) string {
	if v := os.Getenv(k); v != "" {
		return v
	}
	return d
}
