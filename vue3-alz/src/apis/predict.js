import httpRequest from "@/utils/request";

export const predict = (formData) => {
    return httpRequest.post('/predict', formData)
}