import httpRequest from "@/utils/request";

export const login = (data) => {
    return httpRequest.post('/login', data)
}