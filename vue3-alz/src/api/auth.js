import httpRequest from "@/utils/request";

export function login(data) {
    return httpRequest.post('/login', data)
}