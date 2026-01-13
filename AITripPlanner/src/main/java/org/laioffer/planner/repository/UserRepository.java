package org.laioffer.planner.repository;

import org.laioffer.planner.entity.UserEntity;
import org.laioffer.planner.user.model.UserRole;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Optional;

@Repository
public interface UserRepository extends JpaRepository<UserEntity, Long> {

    Optional<UserEntity> findByEmail(String email);

    Optional<UserEntity> findByUsername(String username);

    List<UserEntity> findByRole(UserRole role);

    boolean existsByEmail(String email);

    @Modifying
    @Transactional
    @Query("UPDATE UserEntity u SET u.username = :username WHERE u.email = :email")
    void updateUsernameByEmail(@Param("email") String email, 
                               @Param("username") String username);

    @Modifying
    @Transactional
    @Query("UPDATE UserEntity u SET u.username = :username WHERE u.id = :id")
    void updateUsernameById(@Param("id") Long id,
                           @Param("username") String username);

    Optional<UserEntity> findByResetToken(String resetToken);

    @Modifying
    @Transactional
    @Query("UPDATE UserEntity u SET u.resetToken = :resetToken, u.resetTokenExpiry = :expiry WHERE u.email = :email")
    void updateResetToken(@Param("email") String email,
                         @Param("resetToken") String resetToken,
                         @Param("expiry") java.time.LocalDateTime expiry);

    @Modifying
    @Transactional
    @Query("UPDATE UserEntity u SET u.password = :password, u.resetToken = null, u.resetTokenExpiry = null WHERE u.id = :id")
    void updatePasswordAndClearResetToken(@Param("id") Long id,
                                         @Param("password") String password);
}