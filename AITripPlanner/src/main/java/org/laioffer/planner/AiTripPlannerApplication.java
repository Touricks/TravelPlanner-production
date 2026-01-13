package org.laioffer.planner;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableAsync;

@SpringBootApplication
@EnableAsync
public class AiTripPlannerApplication {

    public static void main(String[] args) {
        SpringApplication.run(AiTripPlannerApplication.class, args);
    }

}
