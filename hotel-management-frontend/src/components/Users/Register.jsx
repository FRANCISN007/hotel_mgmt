// src/components/Users/Register.jsx
import React, { useState } from 'react';
import { registerUser } from '../../api/users';

const Register = () => {
    const [formData, setFormData] = useState({
        username: '',
        password: '',
        role: 'user',
        admin_password: ''
    });
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData({ ...formData, [name]: value });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setSuccess('');

        try {
            const data = await registerUser(formData);
            setSuccess('User registered successfully!');
            console.log(data.message);
        } catch (err) {
            setError(err.detail || 'An error occurred.');
        }
    };

    return (
        <div>
            <h2>Register</h2>
            <form onSubmit={handleSubmit}>
                <div>
                    <label>Username</label>
                    <input
                        type="text"
                        name="username"
                        value={formData.username}
                        onChange={handleChange}
                    />
                </div>
                <div>
                    <label>Password</label>
                    <input
                        type="password"
                        name="password"
                        value={formData.password}
                        onChange={handleChange}
                    />
                </div>
                <div>
                    <label>Role</label>
                    <select
                        name="role"
                        value={formData.role}
                        onChange={handleChange}
                    >
                        <option value="user">User</option>
                        <option value="admin">Admin</option>
                    </select>
                </div>
                {formData.role === 'admin' && (
                    <div>
                        <label>Admin Password</label>
                        <input
                            type="password"
                            name="admin_password"
                            value={formData.admin_password}
                            onChange={handleChange}
                        />
                    </div>
                )}
                <button type="submit">Register</button>
            </form>
            {error && <p style={{ color: 'red' }}>{error}</p>}
            {success && <p style={{ color: 'green' }}>{success}</p>}
        </div>
    );
};

export default Register;
