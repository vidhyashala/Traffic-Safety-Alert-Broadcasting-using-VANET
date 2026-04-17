package trafficsafety;

import org.car2x.veins.nodes.Car;
import org.car2x.veins.nodes.World;
import org.car2x.veins.modules.mobility.traci.TraCIScenarioManagerLaunchd;

network TrafficSafetyScenario {
    submodules:
        manager: TraCIScenarioManagerLaunchd {
            parameters:
                @display("p=80,80");
        }
        world: World {
            parameters:
                @display("p=80,170");
        }
}
