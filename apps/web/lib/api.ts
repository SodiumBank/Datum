/**
 * Datum API Client - Typed API client for Datum backend endpoints (Sprint 8).
 */

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

export interface ApiError {
  detail: string;
  status?: number;
}

export class DatumApiError extends Error {
  detail: string;
  status?: number;

  constructor(message: string, detail: string, status?: number) {
    super(message);
    this.name = "DatumApiError";
    this.detail = detail;
    this.status = status;
  }
}

/**
 * API client with typed methods and error handling.
 */
export class DatumApiClient {
  private baseUrl: string;
  private authToken: string | null = null;

  constructor(baseUrl: string = API_BASE) {
    this.baseUrl = baseUrl;
  }

  setAuthToken(token: string | null) {
    this.authToken = token;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const headers: HeadersInit = {
      "Content-Type": "application/json",
      ...options.headers,
    };

    if (this.authToken) {
      headers["Authorization"] = `Bearer ${this.authToken}`;
    }

    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (!response.ok) {
      let detail = response.statusText;
      try {
        const errorData = await response.json();
        detail = errorData.detail || detail;
      } catch {
        // If response is not JSON, use statusText
      }

      throw new DatumApiError(
        `API request failed: ${response.statusText}`,
        detail,
        response.status
      );
    }

    // Handle empty responses (204 No Content)
    if (response.status === 204) {
      return {} as T;
    }

    return response.json();
  }

  // Auth endpoints
  async login(userId: string, role: string) {
    return this.request<{ access_token: string }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ user_id: userId, role }),
    });
  }

  // SOE endpoints
  async evaluateSOE(inputs: {
    industry_profile: string;
    hardware_class?: string;
    inputs: {
      processes?: string[];
      tests_requested?: string[];
      materials?: string[];
      bom_risk_flags?: string[];
    };
    additional_packs?: string[];
    active_profiles?: string[];
    profile_bundle_id?: string;
  }) {
    return this.request<any>("/soe/evaluate", {
      method: "POST",
      body: JSON.stringify(inputs),
    });
  }

  // Plan endpoints
  async generatePlan(quoteId: string) {
    return this.request<any>("/plans/generate", {
      method: "POST",
      body: JSON.stringify({ quote_id: quoteId }),
    });
  }

  async getPlan(planId: string) {
    return this.request<any>(`/plans/${planId}`);
  }

  async listPlans(quoteId?: string) {
    const query = quoteId ? `?quote_id=${quoteId}` : "";
    return this.request<{ plans: any[] }>(`/plans${query}`);
  }

  async updatePlan(planId: string, edits: any) {
    return this.request<any>(`/plans/${planId}`, {
      method: "PATCH",
      body: JSON.stringify(edits),
    });
  }

  async submitPlan(planId: string, reason?: string) {
    return this.request<any>(`/plans/${planId}/submit`, {
      method: "POST",
      body: JSON.stringify({ reason }),
    });
  }

  async approvePlan(planId: string, reason?: string) {
    return this.request<any>(`/plans/${planId}/approve`, {
      method: "POST",
      body: JSON.stringify({ reason }),
    });
  }

  async rejectPlan(planId: string, reason: string) {
    return this.request<any>(`/plans/${planId}/reject`, {
      method: "POST",
      body: JSON.stringify({ reason }),
    });
  }

  // Quote endpoints
  async getQuote(quoteId: string) {
    return this.request<any>(`/quotes/${quoteId}`);
  }

  async listQuotes(status?: string) {
    const query = status ? `?status=${status}` : "";
    return this.request<{ quotes: any[] }>(`/quotes${query}`);
  }

  // Compliance endpoints
  async getComplianceReport(planId: string, format: "html" | "pdf" = "html") {
    return this.request<any>(`/compliance/plans/${planId}/report?format=${format}`);
  }

  async getAuditIntegrity(planId: string) {
    return this.request<any>(`/compliance/plans/${planId}/audit-integrity`);
  }

  // Profile endpoints
  async getProfileState(profileId: string) {
    return this.request<any>(`/profiles/${profileId}/state`);
  }

  async listProfileBundles() {
    return this.request<{ bundles: any[] }>("/profiles/bundles");
  }
}

// Singleton instance
export const apiClient = new DatumApiClient();
