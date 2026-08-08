import axios from 'axios'

// API base URL - configure this to your backend
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
})

// ESG API Service
export const esgService = {
    // Get all companies with pagination
    async getCompanies(page = 1, limit = 20, search = '', filter = 'all') {
        try {
            const response = await api.get('/api/companies', {
                params: { page, limit, search, filter }
            })
            return response.data
        } catch (error) {
            console.error('Error fetching companies:', error)
            throw error
        }
    },

    // Get single company by ID
    async getCompanyById(companyId) {
        try {
            const response = await api.get(`/api/companies/${companyId}`)
            return response.data
        } catch (error) {
            console.error('Error fetching company:', error)
            throw error
        }
    },

    // Get company ESG data
    async getCompanyESGData(companyId) {
        try {
            const response = await api.get(`/api/companies/${companyId}/esg`)
            return response.data
        } catch (error) {
            console.error('Error fetching ESG data:', error)
            throw error
        }
    },

    // Get aggregated statistics
    async getStatistics() {
        try {
            const response = await api.get('/api/statistics')
            return response.data
        } catch (error) {
            console.error('Error fetching statistics:', error)
            throw error
        }
    },

    // Get emissions data for charts
    async getEmissionsData(limit = 10) {
        try {
            const response = await api.get('/api/emissions', { params: { limit } })
            return response.data
        } catch (error) {
            console.error('Error fetching emissions:', error)
            throw error
        }
    },

    // Search companies
    async searchCompanies(query) {
        try {
            const response = await api.get('/api/search', { params: { q: query } })
            return response.data
        } catch (error) {
            console.error('Error searching companies:', error)
            throw error
        }
    },

    // Get companies by pillar scores
    async getCompaniesByPillar(pillar, minScore, maxScore) {
        try {
            const response = await api.get('/api/companies/pillar', {
                params: { pillar, minScore, maxScore }
            })
            return response.data
        } catch (error) {
            console.error('Error fetching by pillar:', error)
            throw error
        }
    },

    // Export data
    async exportData(format = 'csv', filters = {}) {
        try {
            const response = await api.get('/api/export', {
                params: { format, ...filters },
                responseType: 'blob'
            })
            return response.data
        } catch (error) {
            console.error('Error exporting data:', error)
            throw error
        }
    }
}

// Helper function to load data from local JSON files (for development)
export const loadLocalData = async () => {
    try {
        // This would load from your esg_outputs folder
        const response = await fetch('/api/local-data')
        return response.json()
    } catch (error) {
        console.error('Error loading local data:', error)
        return null
    }
}

export default esgService
