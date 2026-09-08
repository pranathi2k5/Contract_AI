import os

base_dir = r"c:\Users\Pranathi\OneDrive\Desktop\ContractAI\backend-springboot"

files = {
"pom.xml": """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>
    <parent>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-parent</artifactId>
        <version>3.2.3</version>
        <relativePath/> <!-- lookup parent from repository -->
    </parent>
    <groupId>com.contractai</groupId>
    <artifactId>backend-springboot</artifactId>
    <version>0.0.1-SNAPSHOT</version>
    <name>ContractAI Backend</name>
    <description>Backend for ContractAI</description>

    <properties>
        <java.version>17</java.version>
        <jjwt.version>0.12.5</jjwt.version>
    </properties>

    <dependencies>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-web</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-data-jpa</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-security</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-validation</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-webflux</artifactId>
        </dependency>

        <dependency>
            <groupId>org.postgresql</groupId>
            <artifactId>postgresql</artifactId>
            <scope>runtime</scope>
        </dependency>

        <dependency>
            <groupId>org.projectlombok</groupId>
            <artifactId>lombok</artifactId>
            <optional>true</optional>
        </dependency>

        <!-- JWT Dependencies -->
        <dependency>
            <groupId>io.jsonwebtoken</groupId>
            <artifactId>jjwt-api</artifactId>
            <version>${jjwt.version}</version>
        </dependency>
        <dependency>
            <groupId>io.jsonwebtoken</groupId>
            <artifactId>jjwt-impl</artifactId>
            <version>${jjwt.version}</version>
            <scope>runtime</scope>
        </dependency>
        <dependency>
            <groupId>io.jsonwebtoken</groupId>
            <artifactId>jjwt-jackson</artifactId>
            <version>${jjwt.version}</version>
            <scope>runtime</scope>
        </dependency>

        <!-- OpenPDF for PDF generation -->
        <dependency>
            <groupId>com.github.librepdf</groupId>
            <artifactId>openpdf</artifactId>
            <version>1.3.35</version>
        </dependency>

        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-test</artifactId>
            <scope>test</scope>
        </dependency>
        <dependency>
            <groupId>org.springframework.security</groupId>
            <artifactId>spring-security-test</artifactId>
            <scope>test</scope>
        </dependency>
    </dependencies>

    <build>
        <plugins>
            <plugin>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-maven-plugin</artifactId>
                <configuration>
                    <excludes>
                        <exclude>
                            <groupId>org.projectlombok</groupId>
                            <artifactId>lombok</artifactId>
                        </exclude>
                    </excludes>
                </configuration>
            </plugin>
        </plugins>
    </build>
</project>
""",

"src/main/resources/application.yml": """spring:
  application:
    name: contractai-backend
  datasource:
    url: jdbc:postgresql://localhost:5432/contractai
    username: postgres
    password: password
    driver-class-name: org.postgresql.Driver
  jpa:
    hibernate:
      ddl-auto: validate
    show-sql: true
    properties:
      hibernate:
        format_sql: true
  servlet:
    multipart:
      max-file-size: 50MB
      max-request-size: 50MB

app:
  jwt:
    secret: 9A3326127B041846A31BC4162DF88D16A192A41865F939A7264A0DB3B123C04F
    expiration-ms: 86400000 # 24 hours
  fastapi:
    url: http://localhost:8000
  upload:
    dir: uploads
""",

"Dockerfile": """FROM maven:3.9.6-eclipse-temurin-17 AS build
WORKDIR /app
COPY pom.xml .
RUN mvn dependency:go-offline
COPY src ./src
RUN mvn clean package -DskipTests

FROM eclipse-temurin:17-jre-jammy
WORKDIR /app
COPY --from=build /app/target/*.jar app.jar
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "app.jar"]
""",

"src/main/java/com/contractai/ContractAiApplication.java": """package com.contractai;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class ContractAiApplication {
    public static void main(String[] args) {
        SpringApplication.run(ContractAiApplication.class, args);
    }
}
""",

"src/main/java/com/contractai/config/SecurityConfig.java": """package com.contractai.config;

import com.contractai.security.JwtAuthFilter;
import lombok.RequiredArgsConstructor;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.config.annotation.authentication.configuration.AuthenticationConfiguration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configurers.AbstractHttpConfigurer;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;
import org.springframework.web.cors.CorsConfiguration;
import org.springframework.web.cors.CorsConfigurationSource;
import org.springframework.web.cors.UrlBasedCorsConfigurationSource;

import java.util.List;

@Configuration
@EnableWebSecurity
@RequiredArgsConstructor
public class SecurityConfig {

    private final JwtAuthFilter jwtAuthFilter;

    @Bean
    public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
        http
            .csrf(AbstractHttpConfigurer::disable)
            .cors(cors -> cors.configurationSource(corsConfigurationSource()))
            .sessionManagement(session -> session.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/api/auth/**").permitAll()
                .anyRequest().authenticated()
            )
            .addFilterBefore(jwtAuthFilter, UsernamePasswordAuthenticationFilter.class);
        return http.build();
    }

    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    @Bean
    public AuthenticationManager authenticationManager(AuthenticationConfiguration config) throws Exception {
        return config.getAuthenticationManager();
    }
    
    @Bean
    public CorsConfigurationSource corsConfigurationSource() {
        CorsConfiguration config = new CorsConfiguration();
        config.setAllowedOrigins(List.of("*"));
        config.setAllowedMethods(List.of("GET", "POST", "PUT", "DELETE", "OPTIONS"));
        config.setAllowedHeaders(List.of("*"));
        UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
        source.registerCorsConfiguration("/**", config);
        return source;
    }
}
""",

"src/main/java/com/contractai/config/JwtConfig.java": """package com.contractai.config;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;

@Data
@Configuration
@ConfigurationProperties(prefix = "app.jwt")
public class JwtConfig {
    private String secret;
    private long expirationMs;
}
""",

"src/main/java/com/contractai/config/WebClientConfig.java": """package com.contractai.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.reactive.function.client.WebClient;

@Configuration
public class WebClientConfig {

    @Value("${app.fastapi.url}")
    private String fastApiUrl;

    @Bean
    public WebClient webClient() {
        return WebClient.builder()
                .baseUrl(fastApiUrl)
                .codecs(configurer -> configurer
                        .defaultCodecs()
                        .maxInMemorySize(16 * 1024 * 1024))
                .build();
    }
}
""",

"src/main/java/com/contractai/security/JwtTokenProvider.java": """package com.contractai.security;

import com.contractai.config.JwtConfig;
import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import jakarta.annotation.PostConstruct;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.stereotype.Component;

import javax.crypto.SecretKey;
import java.nio.charset.StandardCharsets;
import java.util.Date;

@Component
@RequiredArgsConstructor
public class JwtTokenProvider {

    private final JwtConfig jwtConfig;
    private SecretKey key;

    @PostConstruct
    protected void init() {
        key = Keys.hmacShaKeyFor(jwtConfig.getSecret().getBytes(StandardCharsets.UTF_8));
    }

    public String generateToken(String email, String userId) {
        Date now = new Date();
        Date validity = new Date(now.getTime() + jwtConfig.getExpirationMs());

        return Jwts.builder()
                .subject(email)
                .claim("userId", userId)
                .issuedAt(now)
                .expiration(validity)
                .signWith(key)
                .compact();
    }

    public String getEmailFromToken(String token) {
        Claims claims = Jwts.parser()
                .verifyWith(key)
                .build()
                .parseSignedClaims(token)
                .getPayload();
        return claims.getSubject();
    }

    public boolean validateToken(String token, UserDetails userDetails) {
        try {
            String email = getEmailFromToken(token);
            return (email.equals(userDetails.getUsername()) && !isTokenExpired(token));
        } catch (Exception e) {
            return false;
        }
    }

    private boolean isTokenExpired(String token) {
        Claims claims = Jwts.parser()
                .verifyWith(key)
                .build()
                .parseSignedClaims(token)
                .getPayload();
        return claims.getExpiration().before(new Date());
    }
}
""",

"src/main/java/com/contractai/security/UserDetailsServiceImpl.java": """package com.contractai.security;

import com.contractai.model.User;
import com.contractai.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.stereotype.Service;

import java.util.Collections;

@Service
@RequiredArgsConstructor
public class UserDetailsServiceImpl implements UserDetailsService {

    private final UserRepository userRepository;

    @Override
    public UserDetails loadUserByUsername(String email) throws UsernameNotFoundException {
        User user = userRepository.findByEmail(email)
                .orElseThrow(() -> new UsernameNotFoundException("User Not Found with email: " + email));

        return org.springframework.security.core.userdetails.User.builder()
                .username(user.getEmail())
                .password(user.getPasswordHash())
                .authorities(Collections.emptyList())
                .build();
    }
}
""",

"src/main/java/com/contractai/security/JwtAuthFilter.java": """package com.contractai.security;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.lang.NonNull;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.web.authentication.WebAuthenticationDetailsSource;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;

@Component
@RequiredArgsConstructor
public class JwtAuthFilter extends OncePerRequestFilter {

    private final JwtTokenProvider jwtTokenProvider;
    private final UserDetailsServiceImpl userDetailsService;

    @Override
    protected void doFilterInternal(@NonNull HttpServletRequest request,
                                    @NonNull HttpServletResponse response,
                                    @NonNull FilterChain filterChain) throws ServletException, IOException {
        String authHeader = request.getHeader("Authorization");
        String token = null;
        String email = null;

        if (authHeader != null && authHeader.startsWith("Bearer ")) {
            token = authHeader.substring(7);
            try {
                email = jwtTokenProvider.getEmailFromToken(token);
            } catch (Exception ignored) {
            }
        }

        if (email != null && SecurityContextHolder.getContext().getAuthentication() == null) {
            UserDetails userDetails = userDetailsService.loadUserByUsername(email);

            if (jwtTokenProvider.validateToken(token, userDetails)) {
                UsernamePasswordAuthenticationToken authToken = new UsernamePasswordAuthenticationToken(
                        userDetails, null, userDetails.getAuthorities());
                authToken.setDetails(new WebAuthenticationDetailsSource().buildDetails(request));
                SecurityContextHolder.getContext().setAuthentication(authToken);
            }
        }
        filterChain.doFilter(request, response);
    }
}
""",

"src/main/java/com/contractai/model/User.java": """package com.contractai.model;

import jakarta.persistence.*;
import lombok.*;
import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.UpdateTimestamp;

import java.time.OffsetDateTime;
import java.util.UUID;

@Entity
@Table(name = "users")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class User {
    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(nullable = false, unique = true)
    private String email;

    @Column(name = "password_hash", nullable = false)
    private String passwordHash;

    @Column(name = "full_name", nullable = false)
    private String fullName;

    @CreationTimestamp
    @Column(name = "created_at", updatable = false)
    private OffsetDateTime createdAt;

    @UpdateTimestamp
    @Column(name = "updated_at")
    private OffsetDateTime updatedAt;
}
""",

"src/main/java/com/contractai/model/Contract.java": """package com.contractai.model;

import jakarta.persistence.*;
import lombok.*;
import org.hibernate.annotations.CreationTimestamp;

import java.time.OffsetDateTime;
import java.util.UUID;

@Entity
@Table(name = "contracts")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class Contract {
    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id", nullable = false)
    private User user;

    @Column(length = 500)
    private String title;

    @Column(name = "file_name", nullable = false, length = 500)
    private String fileName;

    @Column(name = "file_type", nullable = false, length = 20)
    private String fileType;

    @Column(name = "file_path", nullable = false, length = 1000)
    private String filePath;

    @Column(name = "extracted_text", columnDefinition = "TEXT")
    private String extractedText;

    @Column(name = "contract_type", length = 100)
    private String contractType;

    @Column(name = "user_role", nullable = false, length = 20)
    private String userRole;

    @Column(length = 30)
    private String status;

    @Column(name = "party_a", length = 500)
    private String partyA;

    @Column(name = "party_b", length = 500)
    private String partyB;

    @CreationTimestamp
    @Column(name = "uploaded_at", updatable = false)
    private OffsetDateTime uploadedAt;

    @Column(name = "analyzed_at")
    private OffsetDateTime analyzedAt;
}
""",

"src/main/java/com/contractai/model/AnalysisResult.java": """package com.contractai.model;

import jakarta.persistence.*;
import lombok.*;
import org.hibernate.annotations.CreationTimestamp;

import java.time.OffsetDateTime;
import java.util.UUID;

@Entity
@Table(name = "analysis_results")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class AnalysisResult {
    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "contract_id", nullable = false)
    private Contract contract;

    @Column(name = "overall_risk_score", nullable = false, precision = 5, scale = 2)
    private Double overallRiskScore;

    @Column(name = "risk_level", nullable = false, length = 20)
    private String riskLevel;

    @Column(columnDefinition = "TEXT")
    private String summary;

    @Column(name = "contract_type_detected", length = 100)
    private String contractTypeDetected;

    @Column(name = "total_clauses_found")
    private Integer totalClausesFound;

    @Column(name = "risky_clauses_count")
    private Integer riskyClausesCount;

    @Column(name = "missing_clauses_count")
    private Integer missingClausesCount;

    @Column(name = "model_used", length = 200)
    private String modelUsed;

    @Column(name = "processing_time_ms")
    private Integer processingTimeMs;

    @CreationTimestamp
    @Column(name = "created_at", updatable = false)
    private OffsetDateTime createdAt;
}
""",

"src/main/java/com/contractai/model/RiskClause.java": """package com.contractai.model;

import jakarta.persistence.*;
import lombok.*;
import org.hibernate.annotations.CreationTimestamp;

import java.time.OffsetDateTime;
import java.util.UUID;

@Entity
@Table(name = "risk_clauses")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class RiskClause {
    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "analysis_id", nullable = false)
    private AnalysisResult analysis;

    @Column(name = "clause_id")
    private UUID clauseId;

    @Column(name = "clause_text", nullable = false, columnDefinition = "TEXT")
    private String clauseText;

    @Column(name = "clause_type", nullable = false, length = 100)
    private String clauseType;

    @Column(name = "risk_score", nullable = false, precision = 5, scale = 2)
    private Double riskScore;

    @Column(name = "risk_category", nullable = false, length = 50)
    private String riskCategory;

    @Column(nullable = false, length = 20)
    private String severity;

    @Column(columnDefinition = "TEXT")
    private String explanation;

    @Column(columnDefinition = "TEXT")
    private String suggestion;

    @CreationTimestamp
    @Column(name = "created_at", updatable = false)
    private OffsetDateTime createdAt;
}
""",

"src/main/java/com/contractai/model/MissingClause.java": """package com.contractai.model;

import jakarta.persistence.*;
import lombok.*;
import org.hibernate.annotations.CreationTimestamp;

import java.time.OffsetDateTime;
import java.util.UUID;

@Entity
@Table(name = "missing_clauses")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class MissingClause {
    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "analysis_id", nullable = false)
    private AnalysisResult analysis;

    @Column(name = "clause_name", nullable = false, length = 255)
    private String clauseName;

    @Column(nullable = false, length = 20)
    private String importance;

    @Column(columnDefinition = "TEXT")
    private String description;

    @Column(name = "template_text", columnDefinition = "TEXT")
    private String templateText;

    @Column(name = "max_similarity_score", precision = 5, scale = 4)
    private Double maxSimilarityScore;

    @CreationTimestamp
    @Column(name = "created_at", updatable = false)
    private OffsetDateTime createdAt;
}
""",

"src/main/java/com/contractai/model/ApplicableLaw.java": """package com.contractai.model;

import jakarta.persistence.*;
import lombok.*;
import org.hibernate.annotations.CreationTimestamp;

import java.time.OffsetDateTime;
import java.util.UUID;

@Entity
@Table(name = "applicable_laws")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ApplicableLaw {
    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "analysis_id", nullable = false)
    private AnalysisResult analysis;

    @Column(name = "clause_id")
    private UUID clauseId;

    @Column(name = "clause_text", columnDefinition = "TEXT")
    private String clauseText;

    @Column(name = "law_name", nullable = false, length = 500)
    private String lawName;

    @Column(name = "act_name", nullable = false, length = 500)
    private String actName;

    @Column(name = "section_number", length = 100)
    private String sectionNumber;

    @Column(name = "section_title", length = 500)
    private String sectionTitle;

    @Column(name = "relevance_score", precision = 5, scale = 2)
    private Double relevanceScore;

    @Column(nullable = false, columnDefinition = "TEXT")
    private String reason;

    @Column(length = 500)
    private String source;

    @CreationTimestamp
    @Column(name = "created_at", updatable = false)
    private OffsetDateTime createdAt;
}
""",

"src/main/java/com/contractai/model/ChatSession.java": """package com.contractai.model;

import jakarta.persistence.*;
import lombok.*;
import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.UpdateTimestamp;

import java.time.OffsetDateTime;
import java.util.UUID;

@Entity
@Table(name = "chat_sessions")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ChatSession {
    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id", nullable = false)
    private User user;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "contract_id")
    private Contract contract;

    @Column(length = 500)
    private String title;

    @CreationTimestamp
    @Column(name = "created_at", updatable = false)
    private OffsetDateTime createdAt;

    @UpdateTimestamp
    @Column(name = "updated_at")
    private OffsetDateTime updatedAt;
}
""",

"src/main/java/com/contractai/model/ChatMessage.java": """package com.contractai.model;

import jakarta.persistence.*;
import lombok.*;
import org.hibernate.annotations.CreationTimestamp;

import java.time.OffsetDateTime;
import java.util.UUID;

@Entity
@Table(name = "chat_messages")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ChatMessage {
    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "session_id", nullable = false)
    private ChatSession session;

    @Column(nullable = false, length = 20)
    private String role;

    @Column(nullable = false, columnDefinition = "TEXT")
    private String content;

    @Column(columnDefinition = "jsonb")
    private String sources;

    @CreationTimestamp
    @Column(name = "created_at", updatable = false)
    private OffsetDateTime createdAt;
}
""",

"src/main/java/com/contractai/dto/RegisterRequest.java": """package com.contractai.dto;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import lombok.Data;

@Data
public class RegisterRequest {
    @NotBlank
    @Email
    private String email;

    @NotBlank
    private String password;

    @NotBlank
    private String fullName;
}
""",

"src/main/java/com/contractai/dto/LoginRequest.java": """package com.contractai.dto;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import lombok.Data;

@Data
public class LoginRequest {
    @NotBlank
    @Email
    private String email;

    @NotBlank
    private String password;
}
""",

"src/main/java/com/contractai/dto/AuthResponse.java": """package com.contractai.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class AuthResponse {
    private String token;
    private String userId;
    private String email;
    private String fullName;
}
""",

"src/main/java/com/contractai/dto/ContractUploadResponse.java": """package com.contractai.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.UUID;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ContractUploadResponse {
    private UUID contractId;
    private String fileName;
    private String status;
}
""",

"src/main/java/com/contractai/dto/AnalysisResponse.java": """package com.contractai.dto;

import com.contractai.model.AnalysisResult;
import com.contractai.model.ApplicableLaw;
import com.contractai.model.MissingClause;
import com.contractai.model.RiskClause;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class AnalysisResponse {
    private AnalysisResult result;
    private List<RiskClause> riskClauses;
    private List<MissingClause> missingClauses;
    private List<ApplicableLaw> applicableLaws;
}
""",

"src/main/java/com/contractai/dto/DashboardResponse.java": """package com.contractai.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.Map;
import java.util.List;
import com.contractai.model.RiskClause;
import com.contractai.model.MissingClause;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class DashboardResponse {
    private Double overallRiskScore;
    private String riskLevel;
    private Map<String, Long> riskDistribution;
    private Integer totalClauses;
    private List<RiskClause> riskyClauses;
    private List<MissingClause> missingClauses;
    private String summary;
}
""",

"src/main/java/com/contractai/dto/ChatRequest.java": """package com.contractai.dto;

import lombok.Data;
import java.util.UUID;

@Data
public class ChatRequest {
    private String message;
    private UUID contractId;
    private UUID sessionId;
}
""",

"src/main/java/com/contractai/dto/ChatResponse.java": """package com.contractai.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.UUID;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ChatResponse {
    private String response;
    private UUID sessionId;
    private String sources;
}
""",

"src/main/java/com/contractai/dto/ErrorResponse.java": """package com.contractai.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ErrorResponse {
    private String message;
    private int status;
    private String timestamp;
}
""",

"src/main/java/com/contractai/repository/UserRepository.java": """package com.contractai.repository;

import com.contractai.model.User;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.Optional;
import java.util.UUID;

public interface UserRepository extends JpaRepository<User, UUID> {
    Optional<User> findByEmail(String email);
    boolean existsByEmail(String email);
}
""",

"src/main/java/com/contractai/repository/ContractRepository.java": """package com.contractai.repository;

import com.contractai.model.Contract;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

public interface ContractRepository extends JpaRepository<Contract, UUID> {
    List<Contract> findByUserId(UUID userId);
    Optional<Contract> findByIdAndUserId(UUID id, UUID userId);
}
""",

"src/main/java/com/contractai/repository/AnalysisResultRepository.java": """package com.contractai.repository;

import com.contractai.model.AnalysisResult;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.Optional;
import java.util.UUID;

public interface AnalysisResultRepository extends JpaRepository<AnalysisResult, UUID> {
    Optional<AnalysisResult> findByContractId(UUID contractId);
}
""",

"src/main/java/com/contractai/repository/RiskClauseRepository.java": """package com.contractai.repository;

import com.contractai.model.RiskClause;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;
import java.util.UUID;

public interface RiskClauseRepository extends JpaRepository<RiskClause, UUID> {
    List<RiskClause> findByAnalysisId(UUID analysisId);
}
""",

"src/main/java/com/contractai/repository/MissingClauseRepository.java": """package com.contractai.repository;

import com.contractai.model.MissingClause;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;
import java.util.UUID;

public interface MissingClauseRepository extends JpaRepository<MissingClause, UUID> {
    List<MissingClause> findByAnalysisId(UUID analysisId);
}
""",

"src/main/java/com/contractai/repository/ApplicableLawRepository.java": """package com.contractai.repository;

import com.contractai.model.ApplicableLaw;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;
import java.util.UUID;

public interface ApplicableLawRepository extends JpaRepository<ApplicableLaw, UUID> {
    List<ApplicableLaw> findByAnalysisId(UUID analysisId);
}
""",

"src/main/java/com/contractai/repository/ChatSessionRepository.java": """package com.contractai.repository;

import com.contractai.model.ChatSession;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

public interface ChatSessionRepository extends JpaRepository<ChatSession, UUID> {
    List<ChatSession> findByUserId(UUID userId);
    Optional<ChatSession> findByUserIdAndContractId(UUID userId, UUID contractId);
}
""",

"src/main/java/com/contractai/repository/ChatMessageRepository.java": """package com.contractai.repository;

import com.contractai.model.ChatMessage;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;
import java.util.UUID;

public interface ChatMessageRepository extends JpaRepository<ChatMessage, UUID> {
    List<ChatMessage> findBySessionIdOrderByCreatedAtAsc(UUID sessionId);
}
""",

"src/main/java/com/contractai/exception/GlobalExceptionHandler.java": """package com.contractai.exception;

import com.contractai.dto.ErrorResponse;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ControllerAdvice;
import org.springframework.web.bind.annotation.ExceptionHandler;

import java.time.OffsetDateTime;

@ControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(ResourceNotFoundException.class)
    public ResponseEntity<ErrorResponse> handleResourceNotFoundException(ResourceNotFoundException ex) {
        ErrorResponse error = ErrorResponse.builder()
                .message(ex.getMessage())
                .status(HttpStatus.NOT_FOUND.value())
                .timestamp(OffsetDateTime.now().toString())
                .build();
        return new ResponseEntity<>(error, HttpStatus.NOT_FOUND);
    }

    @ExceptionHandler(UnauthorizedException.class)
    public ResponseEntity<ErrorResponse> handleUnauthorizedException(UnauthorizedException ex) {
        ErrorResponse error = ErrorResponse.builder()
                .message(ex.getMessage())
                .status(HttpStatus.UNAUTHORIZED.value())
                .timestamp(OffsetDateTime.now().toString())
                .build();
        return new ResponseEntity<>(error, HttpStatus.UNAUTHORIZED);
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<ErrorResponse> handleGlobalException(Exception ex) {
        ErrorResponse error = ErrorResponse.builder()
                .message(ex.getMessage())
                .status(HttpStatus.INTERNAL_SERVER_ERROR.value())
                .timestamp(OffsetDateTime.now().toString())
                .build();
        return new ResponseEntity<>(error, HttpStatus.INTERNAL_SERVER_ERROR);
    }
}
""",

"src/main/java/com/contractai/exception/ResourceNotFoundException.java": """package com.contractai.exception;

public class ResourceNotFoundException extends RuntimeException {
    public ResourceNotFoundException(String message) {
        super(message);
    }
}
""",

"src/main/java/com/contractai/exception/UnauthorizedException.java": """package com.contractai.exception;

public class UnauthorizedException extends RuntimeException {
    public UnauthorizedException(String message) {
        super(message);
    }
}
""",

"src/main/java/com/contractai/service/AuthService.java": """package com.contractai.service;

import com.contractai.dto.AuthResponse;
import com.contractai.dto.LoginRequest;
import com.contractai.dto.RegisterRequest;
import com.contractai.model.User;
import com.contractai.repository.UserRepository;
import com.contractai.security.JwtTokenProvider;
import lombok.RequiredArgsConstructor;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class AuthService {

    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;
    private final JwtTokenProvider jwtTokenProvider;
    private final AuthenticationManager authenticationManager;

    public AuthResponse register(RegisterRequest request) {
        if (userRepository.existsByEmail(request.getEmail())) {
            throw new RuntimeException("Email is already in use!");
        }

        User user = User.builder()
                .email(request.getEmail())
                .passwordHash(passwordEncoder.encode(request.getPassword()))
                .fullName(request.getFullName())
                .build();

        userRepository.save(user);

        String token = jwtTokenProvider.generateToken(user.getEmail(), user.getId().toString());

        return AuthResponse.builder()
                .token(token)
                .userId(user.getId().toString())
                .email(user.getEmail())
                .fullName(user.getFullName())
                .build();
    }

    public AuthResponse login(LoginRequest request) {
        authenticationManager.authenticate(
                new UsernamePasswordAuthenticationToken(request.getEmail(), request.getPassword()));

        User user = userRepository.findByEmail(request.getEmail())
                .orElseThrow(() -> new RuntimeException("User not found"));

        String token = jwtTokenProvider.generateToken(user.getEmail(), user.getId().toString());

        return AuthResponse.builder()
                .token(token)
                .userId(user.getId().toString())
                .email(user.getEmail())
                .fullName(user.getFullName())
                .build();
    }
}
""",

"src/main/java/com/contractai/service/ContractService.java": """package com.contractai.service;

import com.contractai.dto.ContractUploadResponse;
import com.contractai.exception.ResourceNotFoundException;
import com.contractai.model.Contract;
import com.contractai.model.User;
import com.contractai.repository.ContractRepository;
import com.contractai.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.List;
import java.util.UUID;

@Service
@RequiredArgsConstructor
public class ContractService {

    private final ContractRepository contractRepository;
    private final UserRepository userRepository;

    @Value("${app.upload.dir}")
    private String uploadDir;

    public ContractUploadResponse uploadContract(MultipartFile file, String title, String userRole, String userEmail) {
        User user = userRepository.findByEmail(userEmail)
                .orElseThrow(() -> new ResourceNotFoundException("User not found"));

        try {
            Path uploadPath = Paths.get(uploadDir);
            if (!Files.exists(uploadPath)) {
                Files.createDirectories(uploadPath);
            }

            String originalFilename = file.getOriginalFilename();
            String fileType = originalFilename != null && originalFilename.toLowerCase().endsWith(".pdf") ? "PDF" : "DOCX";
            String uniqueFileName = UUID.randomUUID() + "_" + originalFilename;
            Path filePath = uploadPath.resolve(uniqueFileName);

            file.transferTo(filePath.toFile());

            Contract contract = Contract.builder()
                    .user(user)
                    .title(title)
                    .fileName(originalFilename)
                    .fileType(fileType)
                    .filePath(filePath.toString())
                    .userRole(userRole)
                    .status("UPLOADED")
                    .build();

            contract = contractRepository.save(contract);

            return ContractUploadResponse.builder()
                    .contractId(contract.getId())
                    .fileName(contract.getFileName())
                    .status(contract.getStatus())
                    .build();
        } catch (IOException e) {
            throw new RuntimeException("Could not store file", e);
        }
    }

    public List<Contract> getContracts(String userEmail) {
        User user = userRepository.findByEmail(userEmail)
                .orElseThrow(() -> new ResourceNotFoundException("User not found"));
        return contractRepository.findByUserId(user.getId());
    }

    public Contract getContractById(UUID id, String userEmail) {
        User user = userRepository.findByEmail(userEmail)
                .orElseThrow(() -> new ResourceNotFoundException("User not found"));
        return contractRepository.findByIdAndUserId(id, user.getId())
                .orElseThrow(() -> new ResourceNotFoundException("Contract not found"));
    }

    public void deleteContract(UUID id, String userEmail) {
        Contract contract = getContractById(id, userEmail);
        try {
            Files.deleteIfExists(Paths.get(contract.getFilePath()));
        } catch (IOException ignored) {}
        contractRepository.delete(contract);
    }
}
""",

"src/main/java/com/contractai/service/AiServiceClient.java": """package com.contractai.service;

import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;

import java.util.Map;

@Service
@RequiredArgsConstructor
public class AiServiceClient {

    private final WebClient webClient;

    public Map<String, Object> analyzeContract(String contractText, String contractType, String userRole) {
        return webClient.post()
                .uri("/ai/analyze")
                .bodyValue(Map.of(
                        "contractText", contractText,
                        "contractType", contractType != null ? contractType : "unknown",
                        "userRole", userRole
                ))
                .retrieve()
                .bodyToMono(Map.class)
                .block();
    }

    public Map<String, Object> chat(String message, String context) {
        return webClient.post()
                .uri("/ai/chat")
                .bodyValue(Map.of(
                        "message", message,
                        "context", context != null ? context : ""
                ))
                .retrieve()
                .bodyToMono(Map.class)
                .block();
    }
}
""",

"src/main/java/com/contractai/service/AnalysisService.java": """package com.contractai.service;

import com.contractai.dto.AnalysisResponse;
import com.contractai.dto.DashboardResponse;
import com.contractai.exception.ResourceNotFoundException;
import com.contractai.model.*;
import com.contractai.repository.*;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.time.OffsetDateTime;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

@Service
@RequiredArgsConstructor
public class AnalysisService {

    private final ContractRepository contractRepository;
    private final AnalysisResultRepository analysisResultRepository;
    private final RiskClauseRepository riskClauseRepository;
    private final MissingClauseRepository missingClauseRepository;
    private final ApplicableLawRepository applicableLawRepository;
    private final AiServiceClient aiServiceClient;

    public AnalysisResponse triggerAnalysis(UUID contractId, String userEmail) {
        Contract contract = contractRepository.findById(contractId)
                .orElseThrow(() -> new ResourceNotFoundException("Contract not found"));

        contract.setStatus("PROCESSING");
        contractRepository.save(contract);

        // Dummy text extraction for now
        String text = "Sample extracted contract text";
        contract.setExtractedText(text);

        try {
            Map<String, Object> aiResponse = aiServiceClient.analyzeContract(text, contract.getContractType(), contract.getUserRole());
            
            // In a real scenario, map the aiResponse fields to the models
            AnalysisResult result = AnalysisResult.builder()
                    .contract(contract)
                    .overallRiskScore(25.0)
                    .riskLevel("LOW")
                    .summary("Sample AI summary")
                    .contractTypeDetected("NDA")
                    .totalClausesFound(10)
                    .riskyClausesCount(1)
                    .missingClausesCount(0)
                    .modelUsed("gpt-4")
                    .processingTimeMs(2000)
                    .build();
            analysisResultRepository.save(result);

            contract.setStatus("ANALYZED");
            contract.setAnalyzedAt(OffsetDateTime.now());
            contractRepository.save(contract);

            return getAnalysisResults(contractId, userEmail);

        } catch (Exception e) {
            contract.setStatus("FAILED");
            contractRepository.save(contract);
            throw new RuntimeException("Analysis failed: " + e.getMessage());
        }
    }

    public AnalysisResponse getAnalysisResults(UUID contractId, String userEmail) {
        AnalysisResult result = analysisResultRepository.findByContractId(contractId)
                .orElseThrow(() -> new ResourceNotFoundException("Analysis result not found"));

        List<RiskClause> riskClauses = riskClauseRepository.findByAnalysisId(result.getId());
        List<MissingClause> missingClauses = missingClauseRepository.findByAnalysisId(result.getId());
        List<ApplicableLaw> applicableLaws = applicableLawRepository.findByAnalysisId(result.getId());

        return AnalysisResponse.builder()
                .result(result)
                .riskClauses(riskClauses)
                .missingClauses(missingClauses)
                .applicableLaws(applicableLaws)
                .build();
    }

    public DashboardResponse getDashboardData(UUID contractId, String userEmail) {
        AnalysisResponse analysis = getAnalysisResults(contractId, userEmail);
        AnalysisResult result = analysis.getResult();

        Map<String, Long> riskDist = new HashMap<>();
        for (RiskClause rc : analysis.getRiskClauses()) {
            riskDist.put(rc.getRiskCategory(), riskDist.getOrDefault(rc.getRiskCategory(), 0L) + 1);
        }

        return DashboardResponse.builder()
                .overallRiskScore(result.getOverallRiskScore())
                .riskLevel(result.getRiskLevel())
                .riskDistribution(riskDist)
                .totalClauses(result.getTotalClausesFound())
                .riskyClauses(analysis.getRiskClauses())
                .missingClauses(analysis.getMissingClauses())
                .summary(result.getSummary())
                .build();
    }
}
""",

"src/main/java/com/contractai/service/ReportService.java": """package com.contractai.service;

import com.contractai.dto.AnalysisResponse;
import com.lowagie.text.Document;
import com.lowagie.text.Paragraph;
import com.lowagie.text.pdf.PdfWriter;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.io.ByteArrayOutputStream;
import java.util.UUID;

@Service
@RequiredArgsConstructor
public class ReportService {

    private final AnalysisService analysisService;

    public byte[] generatePdfReport(UUID contractId, String userEmail) {
        AnalysisResponse analysis = analysisService.getAnalysisResults(contractId, userEmail);

        try (ByteArrayOutputStream out = new ByteArrayOutputStream()) {
            Document document = new Document();
            PdfWriter.getInstance(document, out);
            document.open();

            document.add(new Paragraph("Contract Analysis Report"));
            document.add(new Paragraph("Contract ID: " + contractId));
            document.add(new Paragraph("Risk Level: " + analysis.getResult().getRiskLevel()));
            document.add(new Paragraph("Summary: " + analysis.getResult().getSummary()));

            document.add(new Paragraph("\\nRisky Clauses:"));
            analysis.getRiskClauses().forEach(rc -> {
                try {
                    document.add(new Paragraph("- " + rc.getClauseType() + " (" + rc.getSeverity() + ")"));
                } catch (Exception e) {}
            });

            document.close();
            return out.toByteArray();
        } catch (Exception e) {
            throw new RuntimeException("Could not generate PDF", e);
        }
    }
}
""",

"src/main/java/com/contractai/service/ChatService.java": """package com.contractai.service;

import com.contractai.dto.ChatRequest;
import com.contractai.dto.ChatResponse;
import com.contractai.model.ChatMessage;
import com.contractai.model.ChatSession;
import com.contractai.model.User;
import com.contractai.repository.ChatMessageRepository;
import com.contractai.repository.ChatSessionRepository;
import com.contractai.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Map;
import java.util.UUID;

@Service
@RequiredArgsConstructor
public class ChatService {

    private final ChatSessionRepository chatSessionRepository;
    private final ChatMessageRepository chatMessageRepository;
    private final UserRepository userRepository;
    private final AiServiceClient aiServiceClient;

    public ChatResponse sendMessage(ChatRequest request, String userEmail) {
        User user = userRepository.findByEmail(userEmail)
                .orElseThrow(() -> new RuntimeException("User not found"));

        ChatSession session;
        if (request.getSessionId() != null) {
            session = chatSessionRepository.findById(request.getSessionId())
                    .orElseThrow(() -> new RuntimeException("Session not found"));
        } else {
            session = ChatSession.builder()
                    .user(user)
                    .title("New Chat")
                    .build();
            session = chatSessionRepository.save(session);
        }

        ChatMessage userMsg = ChatMessage.builder()
                .session(session)
                .role("user")
                .content(request.getMessage())
                .build();
        chatMessageRepository.save(userMsg);

        Map<String, Object> aiResponse = aiServiceClient.chat(request.getMessage(), "context");
        String aiReply = aiResponse != null && aiResponse.containsKey("reply") ? aiResponse.get("reply").toString() : "I'm a placeholder reply.";

        ChatMessage botMsg = ChatMessage.builder()
                .session(session)
                .role("assistant")
                .content(aiReply)
                .sources("[]")
                .build();
        chatMessageRepository.save(botMsg);

        return ChatResponse.builder()
                .response(botMsg.getContent())
                .sessionId(session.getId())
                .sources(botMsg.getSources())
                .build();
    }

    public List<ChatSession> getChatHistory(String userEmail) {
        User user = userRepository.findByEmail(userEmail)
                .orElseThrow(() -> new RuntimeException("User not found"));
        return chatSessionRepository.findByUserId(user.getId());
    }

    public List<ChatMessage> getChatMessages(UUID sessionId, String userEmail) {
        return chatMessageRepository.findBySessionIdOrderByCreatedAtAsc(sessionId);
    }
}
""",

"src/main/java/com/contractai/controller/AuthController.java": """package com.contractai.controller;

import com.contractai.dto.AuthResponse;
import com.contractai.dto.LoginRequest;
import com.contractai.dto.RegisterRequest;
import com.contractai.service.AuthService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/auth")
@RequiredArgsConstructor
public class AuthController {

    private final AuthService authService;

    @PostMapping("/register")
    public ResponseEntity<AuthResponse> register(@Valid @RequestBody RegisterRequest request) {
        return ResponseEntity.ok(authService.register(request));
    }

    @PostMapping("/login")
    public ResponseEntity<AuthResponse> login(@Valid @RequestBody LoginRequest request) {
        return ResponseEntity.ok(authService.login(request));
    }
}
""",

"src/main/java/com/contractai/controller/ContractController.java": """package com.contractai.controller;

import com.contractai.dto.ContractUploadResponse;
import com.contractai.model.Contract;
import com.contractai.service.ContractService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.util.List;
import java.util.UUID;

@RestController
@RequestMapping("/api/contracts")
@RequiredArgsConstructor
public class ContractController {

    private final ContractService contractService;

    @PostMapping("/upload")
    public ResponseEntity<ContractUploadResponse> uploadContract(
            @RequestParam("file") MultipartFile file,
            @RequestParam("title") String title,
            @RequestParam("userRole") String userRole,
            Authentication authentication) {
        return ResponseEntity.ok(contractService.uploadContract(file, title, userRole, authentication.getName()));
    }

    @GetMapping
    public ResponseEntity<List<Contract>> getContracts(Authentication authentication) {
        return ResponseEntity.ok(contractService.getContracts(authentication.getName()));
    }

    @GetMapping("/{id}")
    public ResponseEntity<Contract> getContractById(@PathVariable UUID id, Authentication authentication) {
        return ResponseEntity.ok(contractService.getContractById(id, authentication.getName()));
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deleteContract(@PathVariable UUID id, Authentication authentication) {
        contractService.deleteContract(id, authentication.getName());
        return ResponseEntity.noContent().build();
    }
}
""",

"src/main/java/com/contractai/controller/AnalysisController.java": """package com.contractai.controller;

import com.contractai.dto.AnalysisResponse;
import com.contractai.dto.DashboardResponse;
import com.contractai.service.AnalysisService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

import java.util.UUID;

@RestController
@RequestMapping("/api/contracts/{id}")
@RequiredArgsConstructor
public class AnalysisController {

    private final AnalysisService analysisService;

    @PostMapping("/analyze")
    public ResponseEntity<AnalysisResponse> analyzeContract(@PathVariable UUID id, Authentication authentication) {
        return ResponseEntity.ok(analysisService.triggerAnalysis(id, authentication.getName()));
    }

    @GetMapping("/analysis")
    public ResponseEntity<AnalysisResponse> getAnalysis(@PathVariable UUID id, Authentication authentication) {
        return ResponseEntity.ok(analysisService.getAnalysisResults(id, authentication.getName()));
    }

    @GetMapping("/dashboard")
    public ResponseEntity<DashboardResponse> getDashboard(@PathVariable UUID id, Authentication authentication) {
        return ResponseEntity.ok(analysisService.getDashboardData(id, authentication.getName()));
    }
}
""",

"src/main/java/com/contractai/controller/ReportController.java": """package com.contractai.controller;

import com.contractai.service.ReportService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.UUID;

@RestController
@RequestMapping("/api/contracts/{id}/report")
@RequiredArgsConstructor
public class ReportController {

    private final ReportService reportService;

    @GetMapping("/pdf")
    public ResponseEntity<byte[]> getPdfReport(@PathVariable UUID id, Authentication authentication) {
        byte[] pdfBytes = reportService.generatePdfReport(id, authentication.getName());
        return ResponseEntity.ok()
                .header(HttpHeaders.CONTENT_DISPOSITION, "attachment; filename=report.pdf")
                .contentType(MediaType.APPLICATION_PDF)
                .body(pdfBytes);
    }
}
""",

"src/main/java/com/contractai/controller/ChatController.java": """package com.contractai.controller;

import com.contractai.dto.ChatRequest;
import com.contractai.dto.ChatResponse;
import com.contractai.model.ChatMessage;
import com.contractai.model.ChatSession;
import com.contractai.service.ChatService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.UUID;

@RestController
@RequestMapping("/api/chat")
@RequiredArgsConstructor
public class ChatController {

    private final ChatService chatService;

    @PostMapping
    public ResponseEntity<ChatResponse> chat(@RequestBody ChatRequest request, Authentication authentication) {
        return ResponseEntity.ok(chatService.sendMessage(request, authentication.getName()));
    }

    @GetMapping("/history")
    public ResponseEntity<List<ChatSession>> getChatHistory(Authentication authentication) {
        return ResponseEntity.ok(chatService.getChatHistory(authentication.getName()));
    }

    @GetMapping("/history/{sessionId}")
    public ResponseEntity<List<ChatMessage>> getChatMessages(@PathVariable UUID sessionId, Authentication authentication) {
        return ResponseEntity.ok(chatService.getChatMessages(sessionId, authentication.getName()));
    }
}
"""
}

for path, content in files.items():
    full_path = os.path.join(base_dir, path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)
print("Done")
