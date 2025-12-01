import httpRequest from "@/utils/request";

export function getPredictions(params) {
    return httpRequest.get('/Predictions', { params })
}

export function updatePrediction(id, data) {
    return httpRequest.put(`/Predictions/${id}`, data)
}

export function deletePrediction(id) {
    return httpRequest.delete(`/Predicions/${id}`)
}