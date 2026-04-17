packet AlertMessage {
    string alertId;
    string eventType;
    string sourceVehicle;
    int ttl = 5;
    int priority = 3;
    simtime_t generationTime;
}
