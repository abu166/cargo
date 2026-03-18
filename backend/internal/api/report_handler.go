package api

import (
	"net/http"

	"github.com/go-chi/chi/v5"
)

func (s *Server) mountReportRoutes(r chi.Router) {
	r.Get("/reports/dashboard", s.handleDashboardReport)
	r.Get("/reports/finance", s.handleFinanceReport)
	r.Get("/reports/shipments", s.handleDashboardReport)
	r.Get("/reports/status-summary", s.handleStatusSummary)
}

func (s *Server) handleDashboardReport(w http.ResponseWriter, r *http.Request) {
	report, err := s.services.Reports.Dashboard(r.Context())
	if err != nil {
		handleServiceError(w, err)
		return
	}
	writeJSON(w, http.StatusOK, report)
}

func (s *Server) handleFinanceReport(w http.ResponseWriter, r *http.Request) {
	report, err := s.services.Reports.Finance(r.Context())
	if err != nil {
		handleServiceError(w, err)
		return
	}
	writeJSON(w, http.StatusOK, report)
}

func (s *Server) handleStatusSummary(w http.ResponseWriter, r *http.Request) {
	report, err := s.services.Reports.StatusSummary(r.Context())
	if err != nil {
		handleServiceError(w, err)
		return
	}
	writeJSON(w, http.StatusOK, report)
}
