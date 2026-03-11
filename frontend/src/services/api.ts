import axios from "axios";

const API_URL: string = import.meta.env.VITE_API_URL;
const API_KEY: string = import.meta.env.VITE_PUBLIC_API_KEY;

/** Export an axios instance to easily contact our backend API with the correct base URL and headers
* Example usage:
* 
* ```
* try {
*   const res = await api.get("/endpoint/");
*   console.log(res.data); // Do something with the response data
* } catch (error) {
*   console.error("Error fetching data:", error);
* }
* ```
* 
**/
export const api = axios.create({
    baseURL: API_URL,
    headers: {
        "Content-Type": "application/json",
        "X-API-Key": API_KEY,
    },
});