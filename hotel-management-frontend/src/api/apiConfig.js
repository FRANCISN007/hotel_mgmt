// apiConfig.js
export const BASE_URL = "http://localhost:8000";

// In Api.js
import { BASE_URL } from './apiConfig';

const registerUser = async (userData) => {
    const response = await axios.post(`${BASE_URL}/register`, userData);
    return response.data;
};
