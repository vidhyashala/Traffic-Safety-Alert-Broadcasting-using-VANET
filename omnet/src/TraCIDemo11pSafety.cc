#include "TraCIDemo11pSafety.h"

using namespace veins;

Define_Module(veins::TraCIDemo11pSafety);

void TraCIDemo11pSafety::initialize(int stage) {
    BaseWaveApplLayer::initialize(stage);
    if (stage == 0) {
        defaultTtl = par("defaultTtl").intValue();
        rebroadcastDelayMin = par("rebroadcastDelayMin").doubleValue();
        rebroadcastDelayMax = par("rebroadcastDelayMax").doubleValue();
    }
}

void TraCIDemo11pSafety::onWSM(WaveShortMessage* wsm) {
    auto alertId = wsm->getWsmData();
    int ttl = wsm->getPriority();

    if (seenAlerts.count(alertId) > 0) {
        return;
    }
    seenAlerts.insert(alertId);

    if (!shouldForward(alertId, ttl)) {
        return;
    }

    auto* fwd = wsm->dup();
    fwd->setPriority(ttl - 1);
    simtime_t delay = uniform(rebroadcastDelayMin, rebroadcastDelayMax);
    sendDelayedDown(fwd, delay);
}

void TraCIDemo11pSafety::handleSelfMsg(cMessage* msg) {
    BaseWaveApplLayer::handleSelfMsg(msg);
}

void TraCIDemo11pSafety::sendSafetyAlert(const std::string& eventType, int priority, int ttl) {
    auto* wsm = new WaveShortMessage();
    wsm->setWsmData(eventType.c_str());
    wsm->setPriority(ttl);
    wsm->setChannelNumber(Channels::CCH);
    sendDown(wsm);
}

bool TraCIDemo11pSafety::shouldForward(const std::string& alertId, int ttl) const {
    return ttl > 0;
}
