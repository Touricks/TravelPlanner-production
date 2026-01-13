package org.laioffer.planner.user.authentication;

import org.laioffer.planner.entity.UserEntity;
import org.laioffer.planner.repository.UserRepository;
import org.laioffer.planner.user.model.UserRole;
import org.laioffer.planner.user.security.JwtHandler;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.UUID;

@Service
public class AuthenticationService {

  private final AuthenticationManager authenticationManager;
  private final JwtHandler jwtHandler;
  private final PasswordEncoder passwordEncoder;
  private final UserRepository userRepository;
  private final EmailService emailService;

  public AuthenticationService(AuthenticationManager authenticationManager, JwtHandler jwtHandler,
      PasswordEncoder passwordEncoder, UserRepository userRepository, EmailService emailService) {
    this.authenticationManager = authenticationManager;
    this.jwtHandler = jwtHandler;
    this.passwordEncoder = passwordEncoder;
    this.userRepository = userRepository;
    this.emailService = emailService;
  }

  public UserEntity register(String email, String password, UserRole role, String username,
      String firstName, String lastName) throws UserAlreadyExistException {
    if (userRepository.existsByEmail(email)) {
      throw new UserAlreadyExistException();
    }

    UserEntity userEntity = new UserEntity(role, email, username,
        passwordEncoder.encode(password));
    return userRepository.save(userEntity);
  }

  public String login(String email, String password) {
    authenticationManager.authenticate(new UsernamePasswordAuthenticationToken(email, password));
    UserEntity user = userRepository.findByEmail(email)
        .orElseThrow(() -> new RuntimeException("User not found"));
    return jwtHandler.generateToken(email);
  }

  public void initiatePasswordReset(String email) {
    UserEntity user = userRepository.findByEmail(email)
        .orElseThrow(() -> new RuntimeException("User not found with email: " + email));

    String resetToken = UUID.randomUUID().toString();
    LocalDateTime expiry = LocalDateTime.now().plusHours(1);

    userRepository.updateResetToken(email, resetToken, expiry);
    emailService.sendPasswordResetEmail(email, resetToken);
  }

  public void resetPassword(String token, String newPassword) {
    UserEntity user = userRepository.findByResetToken(token)
        .orElseThrow(() -> new RuntimeException("Invalid reset token"));

    if (user.getResetTokenExpiry() == null || user.getResetTokenExpiry().isBefore(LocalDateTime.now())) {
      throw new RuntimeException("Reset token has expired");
    }

    String encodedPassword = passwordEncoder.encode(newPassword);
    userRepository.updatePasswordAndClearResetToken(user.getId(), encodedPassword);
  }
}
