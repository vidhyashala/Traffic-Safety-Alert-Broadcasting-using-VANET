#ifndef __TRAFFICSAFETY_TRACIDEMO11PSAFETY_H_
#define __TRAFFICSAFETY_TRACIDEMO11PSAFETY_H_

#include <set>
#include "veins/modules/application/ieee80211p/BaseWaveApplLayer.h"
#include "veins/modules/messages/WaveShortMessage_m.h"

namespace veins {

class TraCIDemo11pSafety : public BaseWaveApplLayer {
  protected:
    int defaultTtl = 5;
    double rebroadcastDelayMin = 0.01;
    double rebroadcastDelayMax = 0.08;
    std::set<std::string> seenAlerts;

  protected:
    void initialize(int stage) override;
    void onWSM(WaveShortMessage* wsm) override;
    void handleSelfMsg(cMessage* msg) override;

    void sendSafetyAlert(const std::string& eventType, int priority, int ttl);
    bool shouldForward(const std::string& alertId, int ttl) const;
};

} // namespace veins

#endif
