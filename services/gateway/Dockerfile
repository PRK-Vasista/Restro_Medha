FROM golang:1.22-alpine AS build
WORKDIR /src
COPY go.mod .
COPY main.go .
RUN go build -o /gateway main.go

FROM alpine:3.20
COPY --from=build /gateway /gateway
EXPOSE 8080
CMD ["/gateway"]
