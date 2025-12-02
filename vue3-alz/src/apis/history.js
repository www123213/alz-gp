import httpRequest from "@/utils/request";

export const getPredictions = (params) => {
    return httpRequest.get('/Predictions', { params })
}

export const updatePrediction = (id, data) => {
    return httpRequest.put(`/Predictions/${id}`, data)
}

export const deletePrediction = (id) => {
    return httpRequest.delete(`/Predictions/${id}`)
}