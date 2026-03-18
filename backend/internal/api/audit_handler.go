package api

import (
	"net/http"

	"github.com/go-chi/chi/v5"
)

func (s *Server) mountAuditRoutes(r chi.Router) {
	r.Get("/audit/logs", s.handleAuditLogs)
}

func (s *Server) handleAuditLogs(w http.ResponseWriter, r *http.Request) {
	items, err := s.services.Audit.List(r.Context())
	if err != nil {
		handleServiceError(w, err)
		return
	}
	writeJSON(w, http.StatusOK, items)
}
