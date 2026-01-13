package org.laioffer.planner.user.authentication;

import org.laioffer.planner.user.authentication.model.ForgotPasswordRequest;
import org.laioffer.planner.user.authentication.model.LoginRequest;
import org.laioffer.planner.user.authentication.model.LoginResponse;
import org.laioffer.planner.user.authentication.model.RegisterRequest;
import org.laioffer.planner.user.authentication.model.ResetPasswordRequest;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/auth")
public class AuthenticationController {

  private final AuthenticationService authenticationService;

  public AuthenticationController(AuthenticationService authenticationService) {
    this.authenticationService = authenticationService;
  }

  @PostMapping("/register")
  @ResponseStatus(HttpStatus.CREATED)
  public void register(@Valid @RequestBody RegisterRequest body) {
    authenticationService.register(body.email(), body.password(), body.role(), body.username(),
        body.firstName(), body.lastName());
  }

  @PostMapping("/login")
  public LoginResponse login(@Valid @RequestBody LoginRequest body) {
    return new LoginResponse(authenticationService.login(body.email(), body.password()));
  }

  @PostMapping("/forgot-password")
  public Map<String, String> forgotPassword(@Valid @RequestBody ForgotPasswordRequest body) {
    authenticationService.initiatePasswordReset(body.email());
    return Map.of("message", "Password reset link has been sent to your email");
  }

  @PostMapping("/reset-password")
  public Map<String, String> resetPassword(@Valid @RequestBody ResetPasswordRequest body) {
    authenticationService.resetPassword(body.token(), body.newPassword());
    return Map.of("message", "Password has been reset successfully");
  }
}
