package main

import (
	"net/http"
	"os"

	"github.com/gleich/logoru"
	"github.com/gorilla/handlers"
	"github.com/spf13/pflag"
)

func main() {
	var webserverPort *string = pflag.String("webserverPort", "8080", "HTTP port that the webserver listens on; the default is 8080")
	var webserverDirectory *string = pflag.String("webserverDirectory", ".", "HTTP directory to be served from; the default is '.'.")
	pflag.Parse()

	logoru.Info("Go Webserver listening on tcp port", *webserverPort)

	// serve `webserver_directory` as the http root: / and log all to os.Stdout
	http.Handle("/", handlers.CombinedLoggingHandler(os.Stdout, http.FileServer(http.Dir(*webserverDirectory))))
	// serve from all external ipv4 and ipv6 addresses
	http.ListenAndServe(":"+*webserverPort, nil)

}
