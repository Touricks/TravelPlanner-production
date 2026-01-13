package org.laioffer.planner.config;

import org.springframework.context.annotation.Configuration;
import org.springframework.data.jpa.repository.config.EnableJpaAuditing;
import org.springframework.data.jpa.repository.config.EnableJpaRepositories;
import org.springframework.transaction.annotation.EnableTransactionManagement;

@Configuration
@EnableJpaAuditing
@EnableJpaRepositories(basePackages = "org.laioffer.planner")
@EnableTransactionManagement
public class JpaConfig {
    // JPA configuration for the application
    // - Enables JPA auditing for @CreatedDate and @LastModifiedDate
    // - Enables JPA repositories scanning
    // - Enables transaction management
}