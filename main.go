package main

// 打开系统默认浏览器

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"os"
	"os/exec"
	"runtime"
)

type Client struct {
	StartUrl string `json:"start_url"`
}

var commands = map[string]string{
	"windows": "start",
	"darwin":  "open",
	"linux":   "xdg-open",
}

func OpenUrl(uri string) error {
	run, ok := commands[runtime.GOOS]
	if !ok {
		return fmt.Errorf("don't know how to open things on %s platform", runtime.GOOS)
	}

	cmd := exec.Command(run, uri)
	return cmd.Start()
}

func ReadJsonFile(Filepath string, JsonModel interface{}) {
	jsonFile, err := os.Open(Filepath)
	if err != nil {
		fmt.Println(err)
	}
	defer jsonFile.Close()
	byteValue, _ := ioutil.ReadAll(jsonFile)
	// var JsonModel map[string]interface{}
	json.Unmarshal([]byte(byteValue), &JsonModel)
}

func StartServer() error {
	cmd := exec.Command("./WebServer")
	return cmd.Start()
}

func main() {
	// StartServer()
	var JsonModel Client
	ReadJsonFile("config/client.json", &JsonModel)
	fmt.Println(JsonModel.StartUrl)
	OpenUrl(JsonModel.StartUrl)
}
