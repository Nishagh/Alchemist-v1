package main

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"strings"
	"time"

	"cloud.google.com/go/storage"
	"github.com/higress-group/openapi-to-mcpserver/pkg/converter"
	"github.com/higress-group/openapi-to-mcpserver/pkg/models"
	"github.com/higress-group/openapi-to-mcpserver/pkg/parser"
	"google.golang.org/api/option"
	"gopkg.in/yaml.v3"
)

type ConversionRequest struct {
	OpenAPISpec    string `json:"openapi_spec"`
	ServerName     string `json:"server_name,omitempty"`
	ToolPrefix     string `json:"tool_prefix,omitempty"`
	Format         string `json:"format,omitempty"`
	Validate       bool   `json:"validate,omitempty"`
	TemplateConfig string `json:"template_config,omitempty"`
}

type UploadRequest struct {
	FileContent string `json:"file_content"`
	FileName    string `json:"file_name,omitempty"`
	Format      string `json:"format,omitempty"`
}

type ConversionResponse struct {
	Success           bool   `json:"success"`
	MCPConfig         string `json:"mcp_config,omitempty"`
	Error             string `json:"error,omitempty"`
	Format            string `json:"format"`
	ServerName        string `json:"server_name"`
	OpenAPIFileURL    string `json:"openapi_file_url,omitempty"`
	MCPConfigFileURL  string `json:"mcp_config_file_url,omitempty"`
}

type UploadResponse struct {
	Success    bool   `json:"success"`
	Error      string `json:"error,omitempty"`
	FileType   string `json:"file_type"`
	PublicURL  string `json:"public_url,omitempty"`
	FileName   string `json:"file_name,omitempty"`
}

type ConversionService struct {
	storageClient *storage.Client
	bucketName    string
}

func main() {
	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	bucketName := os.Getenv("FIREBASE_STORAGE_BUCKET")
	if bucketName == "" {
		log.Fatal("FIREBASE_STORAGE_BUCKET environment variable is required")
	}

	// Initialize Firebase Storage client
	ctx := context.Background()
	var storageClient *storage.Client
	var err error

	// If running locally, use service account key
	if serviceAccountPath := os.Getenv("GOOGLE_APPLICATION_CREDENTIALS"); serviceAccountPath != "" {
		storageClient, err = storage.NewClient(ctx, option.WithCredentialsFile(serviceAccountPath))
	} else {
		// Use default credentials (works in Cloud Run)
		storageClient, err = storage.NewClient(ctx)
	}

	if err != nil {
		log.Fatalf("Failed to create storage client: %v", err)
	}

	service := &ConversionService{
		storageClient: storageClient,
		bucketName:    bucketName,
	}

	http.HandleFunc("/convert", service.handleConvert)
	http.HandleFunc("/upload", service.handleUpload)
	http.HandleFunc("/health", handleHealth)

	log.Printf("Server starting on port %s", port)
	log.Printf("Using Firebase Storage bucket: %s", bucketName)
	log.Fatal(http.ListenAndServe(":"+port, nil))
}

func (s *ConversionService) handleConvert(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	// Parse JSON request
	var req ConversionRequest
	err := json.NewDecoder(r.Body).Decode(&req)
	if err != nil {
		respondWithError(w, "Invalid JSON request", http.StatusBadRequest)
		return
	}

	// Validate required fields
	if req.OpenAPISpec == "" {
		respondWithError(w, "openapi_spec is required", http.StatusBadRequest)
		return
	}

	// Set defaults
	if req.ServerName == "" {
		req.ServerName = "openapi-server"
	}
	if req.Format == "" {
		req.Format = "yaml"
	}

	ctx := context.Background()

	// Generate unique filenames with timestamp
	timestamp := time.Now().Format("20060102-150405")
	openAPIFileName := fmt.Sprintf("openapi/%s-%s.yaml", req.ServerName, timestamp)
	mcpConfigFileName := fmt.Sprintf("mcp-configs/%s-%s.%s", req.ServerName, timestamp, req.Format)

	// Save OpenAPI spec to Firebase Storage
	openAPIFileURL, err := s.saveToStorage(ctx, openAPIFileName, []byte(req.OpenAPISpec), "application/x-yaml")
	if err != nil {
		respondWithError(w, fmt.Sprintf("Failed to save OpenAPI spec: %v", err), http.StatusInternalServerError)
		return
	}

	// Convert the specification
	mcpConfig, err := convertOpenAPIToMCP(req.OpenAPISpec, req.ServerName, req.ToolPrefix, req.Format, req.Validate, req.TemplateConfig)
	if err != nil {
		respondWithError(w, fmt.Sprintf("Conversion failed: %v", err), http.StatusBadRequest)
		return
	}

	// Save MCP config to Firebase Storage
	var contentType string
	if req.Format == "json" {
		contentType = "application/json"
	} else {
		contentType = "application/x-yaml"
	}

	mcpConfigFileURL, err := s.saveToStorage(ctx, mcpConfigFileName, []byte(mcpConfig), contentType)
	if err != nil {
		respondWithError(w, fmt.Sprintf("Failed to save MCP config: %v", err), http.StatusInternalServerError)
		return
	}

	// Return successful response
	response := ConversionResponse{
		Success:           true,
		MCPConfig:         mcpConfig,
		Format:            req.Format,
		ServerName:        req.ServerName,
		OpenAPIFileURL:    openAPIFileURL,
		MCPConfigFileURL:  mcpConfigFileURL,
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

func (s *ConversionService) saveToStorage(ctx context.Context, fileName string, data []byte, contentType string) (string, error) {
	// Create object handle
	obj := s.storageClient.Bucket(s.bucketName).Object(fileName)

	// Create writer
	writer := obj.NewWriter(ctx)
	writer.ContentType = contentType
	writer.Metadata = map[string]string{
		"uploaded_at": time.Now().UTC().Format(time.RFC3339),
	}

	// Write data
	if _, err := writer.Write(data); err != nil {
		return "", fmt.Errorf("failed to write to storage: %w", err)
	}

	// Close writer
	if err := writer.Close(); err != nil {
		return "", fmt.Errorf("failed to close storage writer: %w", err)
	}

	// Make object publicly readable (optional - remove if you want private files)
	if err := obj.ACL().Set(ctx, storage.AllUsers, storage.RoleReader); err != nil {
		log.Printf("Warning: Failed to make file public: %v", err)
		// Continue anyway, file is still accessible with proper authentication
	}

	// Generate public URL
	publicURL := fmt.Sprintf("https://storage.googleapis.com/%s/%s", s.bucketName, fileName)
	
	return publicURL, nil
}

func handleHealth(w http.ResponseWriter, r *http.Request) {
	// Set CORS headers
	w.Header().Set("Access-Control-Allow-Origin", "*")
	w.Header().Set("Access-Control-Allow-Methods", "GET, OPTIONS")
	w.Header().Set("Access-Control-Allow-Headers", "Accept, Content-Type, Authorization")
	
	// Handle preflight requests
	if r.Method == http.MethodOptions {
		w.WriteHeader(http.StatusOK)
		return
	}
	
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{"status": "healthy"})
}

func respondWithError(w http.ResponseWriter, message string, statusCode int) {
	response := ConversionResponse{
		Success: false,
		Error:   message,
	}
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(statusCode)
	json.NewEncoder(w).Encode(response)
}

func convertOpenAPIToMCP(openAPIContent, serverName, toolPrefix, format string, validate bool, templateConfig string) (string, error) {
	// Create a temporary file for the OpenAPI content
	tmpFile, err := os.CreateTemp("", "openapi-*.yaml")
	if err != nil {
		return "", fmt.Errorf("failed to create temporary file: %w", err)
	}
	defer os.Remove(tmpFile.Name())
	defer tmpFile.Close()

	// Write OpenAPI content to temporary file
	_, err = tmpFile.WriteString(openAPIContent)
	if err != nil {
		return "", fmt.Errorf("failed to write temporary file: %w", err)
	}
	tmpFile.Close()

	// Create parser and set validation option
	p := parser.NewParser()
	p.SetValidation(validate)

	// Parse the OpenAPI specification
	err = p.ParseFile(tmpFile.Name())
	if err != nil {
		return "", fmt.Errorf("failed to parse OpenAPI specification: %w", err)
	}

	// Handle template if provided
	var templatePath string
	if templateConfig != "" {
		tmpTemplate, err := os.CreateTemp("", "template-*.yaml")
		if err != nil {
			return "", fmt.Errorf("failed to create template file: %w", err)
		}
		defer os.Remove(tmpTemplate.Name())
		defer tmpTemplate.Close()

		_, err = tmpTemplate.WriteString(templateConfig)
		if err != nil {
			return "", fmt.Errorf("failed to write template file: %w", err)
		}
		tmpTemplate.Close()
		templatePath = tmpTemplate.Name()
	}

	// Create converter
	c := converter.NewConverter(p, models.ConvertOptions{
		ServerName:     serverName,
		ToolNamePrefix: toolPrefix,
		TemplatePath:   templatePath,
	})

	// Convert the OpenAPI specification to an MCP configuration
	config, err := c.Convert()
	if err != nil {
		return "", fmt.Errorf("failed to convert OpenAPI specification: %w", err)
	}

	// Marshal the configuration based on the requested format
	var data []byte
	if format == "json" {
		data, err = json.MarshalIndent(config, "", "  ")
	} else {
		var buffer bytes.Buffer
		encoder := yaml.NewEncoder(&buffer)
		encoder.SetIndent(2)
		
		if err := encoder.Encode(config); err != nil {
			return "", fmt.Errorf("failed to encode YAML: %w", err)
		}
		data = buffer.Bytes()
	}
	if err != nil {
		return "", fmt.Errorf("failed to marshal MCP configuration: %w", err)
	}

	return string(data), nil
}

func (s *ConversionService) handleUpload(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	// Parse JSON request
	var req UploadRequest
	err := json.NewDecoder(r.Body).Decode(&req)
	if err != nil {
		respondWithUploadError(w, "Invalid JSON request", http.StatusBadRequest)
		return
	}

	// Validate required fields
	if req.FileContent == "" {
		respondWithUploadError(w, "file_content is required", http.StatusBadRequest)
		return
	}

	// Detect file type
	fileType, err := detectFileType(req.FileContent)
	if err != nil {
		respondWithUploadError(w, fmt.Sprintf("File validation failed: %v", err), http.StatusBadRequest)
		return
	}

	// Set defaults based on file type
	if req.Format == "" {
		if fileType == "openapi" {
			req.Format = "yaml"
		} else {
			// Detect format from content for MCP files
			req.Format = detectMCPFormat(req.FileContent)
		}
	}

	if req.FileName == "" {
		req.FileName = fmt.Sprintf("uploaded-file-%s", time.Now().Format("20060102-150405"))
	}

	ctx := context.Background()

	// Generate filename based on file type
	var fileName string
	var contentType string
	
	if fileType == "openapi" {
		fileName = fmt.Sprintf("openapi/%s.%s", req.FileName, req.Format)
		if req.Format == "json" {
			contentType = "application/json"
		} else {
			contentType = "application/x-yaml"
		}
	} else {
		fileName = fmt.Sprintf("mcp-configs/%s.%s", req.FileName, req.Format)
		if req.Format == "json" {
			contentType = "application/json"
		} else {
			contentType = "application/x-yaml"
		}
	}

	// Save file to Firebase Storage
	publicURL, err := s.saveToStorage(ctx, fileName, []byte(req.FileContent), contentType)
	if err != nil {
		respondWithUploadError(w, fmt.Sprintf("Failed to save file: %v", err), http.StatusInternalServerError)
		return
	}

	// Return successful response
	response := UploadResponse{
		Success:   true,
		FileType:  fileType,
		PublicURL: publicURL,
		FileName:  fileName,
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

func detectFileType(content string) (string, error) {
	// Try to parse as JSON first
	var jsonData map[string]interface{}
	if err := json.Unmarshal([]byte(content), &jsonData); err == nil {
		// Check for OpenAPI indicators
		if openapi, exists := jsonData["openapi"]; exists {
			if openapiStr, ok := openapi.(string); ok && strings.HasPrefix(openapiStr, "3.") {
				return "openapi", nil
			}
		}
		if swagger, exists := jsonData["swagger"]; exists {
			if swaggerStr, ok := swagger.(string); ok && strings.HasPrefix(swaggerStr, "2.") {
				return "openapi", nil
			}
		}
		
		// Check for MCP config indicators
		if server, exists := jsonData["server"]; exists {
			if serverMap, ok := server.(map[string]interface{}); ok {
				if _, nameExists := serverMap["name"]; nameExists {
					return "mcp_config", nil
				}
			}
		}
		if tools, exists := jsonData["tools"]; exists {
			if _, ok := tools.([]interface{}); ok {
				return "mcp_config", nil
			}
		}
		
		return "", fmt.Errorf("unrecognized JSON file format")
	}

	// Try to parse as YAML
	var yamlData map[string]interface{}
	if err := yaml.Unmarshal([]byte(content), &yamlData); err == nil {
		// Check for OpenAPI indicators
		if openapi, exists := yamlData["openapi"]; exists {
			if openapiStr, ok := openapi.(string); ok && strings.HasPrefix(openapiStr, "3.") {
				return "openapi", nil
			}
		}
		if swagger, exists := yamlData["swagger"]; exists {
			if swaggerStr, ok := swagger.(string); ok && strings.HasPrefix(swaggerStr, "2.") {
				return "openapi", nil
			}
		}
		
		// Check for MCP config indicators
		if server, exists := yamlData["server"]; exists {
			if serverMap, ok := server.(map[string]interface{}); ok {
				if _, nameExists := serverMap["name"]; nameExists {
					return "mcp_config", nil
				}
			}
		}
		if tools, exists := yamlData["tools"]; exists {
			if _, ok := tools.([]interface{}); ok {
				return "mcp_config", nil
			}
		}
		
		return "", fmt.Errorf("unrecognized YAML file format")
	}

	return "", fmt.Errorf("file is neither valid JSON nor YAML")
}

func detectMCPFormat(content string) string {
	// Try JSON first
	var jsonData interface{}
	if err := json.Unmarshal([]byte(content), &jsonData); err == nil {
		return "json"
	}
	
	// Default to YAML
	return "yaml"
}

func respondWithUploadError(w http.ResponseWriter, message string, statusCode int) {
	response := UploadResponse{
		Success: false,
		Error:   message,
	}
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(statusCode)
	json.NewEncoder(w).Encode(response)
}