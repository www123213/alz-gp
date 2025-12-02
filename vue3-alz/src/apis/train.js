import httpRequest from "@/utils/request";

export const getTrainLog = () => {
    return httpRequest.get('/train/log')
}

export const startTrain = (formData) => {
    return httpRequest.post('/train', formData)
}

export const stopTrain = () => {
    return httpRequest.post('/train/stop')
}