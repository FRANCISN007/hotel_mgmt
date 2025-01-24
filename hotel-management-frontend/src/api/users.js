// src/api/users.js
import axios from 'axios';

const API_URL = 'http://localhost:8000'; // Update with your backend URL

export const registerUser = async (userData) => {
    try {
        const response = await axios.post(`${API_URL}/user/register/`, userData);
        return response.data;
    } catch (error) {
        throw error.response ? error.response.data : error;
    }
};

export const loginUser = async (credentials) => {
    try {
        const response = await axios.post(`${API_URL}/user/token`, credentials);
        return response.data;
    } catch (error) {
        throw error.response ? error.response.data : error;
    }
};
