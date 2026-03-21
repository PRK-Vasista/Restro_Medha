package main

import (
	"encoding/json"
	"io"
	"log"
	"net/http"
	"os"
	"sync"
	"time"
)

type Event struct {
	MessageID string          `json:"message_id"`
	Source    string          `json:"source_device_id"`
	Sequence  int64           `json:"sequence"`
	SentAt    string          `json:"sent_at"`
	Payload   json.RawMessage `json:"payload"`
}

var (
	mu             sync.Mutex
	events         []Event
	seenMessageIDs = map[string]bool{}
)

func main() {
	mux := http.NewServeMux()
	mux.HandleFunc("/health", health)
	mux.HandleFunc("/sync/events", ingestEvent)
	mux.HandleFunc("/sync/replay", replayEvents)

	port := env("PORT", "8003")
	log.Printf("sync manager listening on :%s", port)
	if err := http.ListenAndServe(":"+port, mux); err != nil {
		log.Fatal(err)
	}
}

func health(w http.ResponseWriter, _ *http.Request) {
	_, _ = io.WriteString(w, `{"status":"ok"}`)
}

func ingestEvent(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		w.WriteHeader(http.StatusMethodNotAllowed)
		return
	}
	var e Event
	if err := json.NewDecoder(r.Body).Decode(&e); err != nil {
		w.WriteHeader(http.StatusBadRequest)
		_, _ = io.WriteString(w, `{"error":"invalid_json"}`)
		return
	}
	if e.SentAt == "" {
		e.SentAt = time.Now().UTC().Format(time.RFC3339)
	}

	mu.Lock()
	defer mu.Unlock()
	if seenMessageIDs[e.MessageID] {
		_, _ = io.WriteString(w, `{"status":"duplicate_ignored"}`)
		return
	}
	seenMessageIDs[e.MessageID] = true
	events = append(events, e)
	_, _ = io.WriteString(w, `{"status":"accepted"}`)
}

func replayEvents(w http.ResponseWriter, r *http.Request) {
	mu.Lock()
	defer mu.Unlock()
	_ = json.NewEncoder(w).Encode(events)
}

func env(k, d string) string {
	if v := os.Getenv(k); v != "" {
		return v
	}
	return d
}
