import httpRequest from "@/utils/request";

export function predict(formData) {
    return httpRequest.post('/predict', formData)
}