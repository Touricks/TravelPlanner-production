package org.laioffer.planner.repository;

import org.laioffer.planner.entity.ItineraryEntity;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

@Repository
public interface ItineraryRepository extends JpaRepository<ItineraryEntity, UUID> {

    // 基本查询 - 查询用户的行程
    List<ItineraryEntity> findByUserId(Long userId);

    // 分页查询用户的行程
    Page<ItineraryEntity> findByUserId(Long userId, Pageable pageable);

    // 按城市查询
    List<ItineraryEntity> findByDestinationCity(String destinationCity);
    List<ItineraryEntity> findByUserIdAndDestinationCity(Long userId, String destinationCity);

    // 权限验证 - 检查行程是否属于用户
    boolean existsByIdAndUserId(UUID itineraryId, Long userId);

    // 统计查询
    long countByUserId(Long userId);

    // 自定义更新操作（参考 UserRepository 的 updateUsernameById 模式）
    @Modifying
    @Transactional
    @Query("UPDATE ItineraryEntity i SET i.destinationCity = :city WHERE i.id = :id")
    void updateDestinationCity(@Param("id") UUID id, @Param("city") String city);

    @Modifying
    @Transactional
    @Query("UPDATE ItineraryEntity i SET i.budgetInCents = :budget WHERE i.id = :id")
    void updateBudget(@Param("id") UUID id, @Param("budget") Integer budget);

    // CRAG Session 关联查询
    Optional<ItineraryEntity> findByCragSessionId(String cragSessionId);

    boolean existsByCragSessionId(String cragSessionId);

    // 按CRAG Session ID和用户ID查询（用于Upsert更新）
    Optional<ItineraryEntity> findByCragSessionIdAndUserId(String cragSessionId, Long userId);
}