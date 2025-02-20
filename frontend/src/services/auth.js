import {api} from './api'

// Object with all auth services
export const authServices = {
    // Asynch register function, takes all data needed for reg
    register: async (data) => {
        const response = await api.post('api/auth/register/', data) // Send post request
        return response.data
    },

    // Asynch login function, takes all data needed for login
    login: async (creds) => {
        const response = await api.post('api/auth/login/', creds)
        return response.data
    },

    // Asynch refresh function, takes all data needed for refresh
    refreshToken: async () => {
        const refresh = localStorage.getItem('refresh')
        const response = await api.post('api/auth/token-refresh/', {refresh}) // Send refresh token in request body
        return response.data
    }
}