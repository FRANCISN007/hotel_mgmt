// Importing React hooks and axios for making HTTP requests
import { useEffect, useState } from 'react'; 
import axios from 'axios';

const UserList = () => {
  const [users, setUsers] = useState([]);  // State to store the list of users
  const [error, setError] = useState('');   // State to handle error messages

  // Fetch users from backend when the component mounts
  useEffect(() => {
    const fetchUsers = async () => {
      try {
        // Sending GET request to the backend's /users/ endpoint
        const response = await axios.get('/api/users/');
        setUsers(response.data);  // Store the user list
      } catch (err) {
        // Set an error message if fetching fails
        setError('Failed to load users');
      }
    };

    fetchUsers();  // Call the function to fetch users
  }, []);

  // Function to handle user deletion
  const handleDelete = async (username) => {
    try {
      // Sending DELETE request to remove the user
      await axios.delete(`/api/users/${username}`);
      setUsers(users.filter(user => user.username !== username));  // Remove deleted user from the list
    } catch (err) {
      // Set an error message if deletion fails
      setError('Failed to delete user');
    }
  };

  return (
    <div>
      <h2>User List</h2>
      {/* Display any error message */}
      {error && <p>{error}</p>}
      
      {/* List of users */}
      <ul>
        {users.map(user => (
          <li key={user.id}>
            {user.username} - {user.role}
            <button onClick={() => handleDelete(user.username)}>Delete</button> {/* Delete button */}
          </li>
        ))}
      </ul>
    </div>
  );
};

export default UserList;
