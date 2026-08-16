package top.zhaizz.client.contract;

import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import top.zhaizz.client.controller.CollectionController;
import top.zhaizz.client.service.CollectionService;
import top.zhaizz.pojo.vo.collection.WishlistAddResultVO;

import java.util.List;

import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

/**
 * 想看加入接口契约测试：统一 Result<T> 包装，业务 VO 不重复嵌套 code/message/data
 */
class CollectionWishlistContractTest {

    private CollectionService collectionService;
    private MockMvc mockMvc;

    @BeforeEach
    void setUp() {
        collectionService = mock(CollectionService.class);
        mockMvc = MockMvcBuilders.standaloneSetup(new CollectionController(collectionService)).build();
        SecurityContextHolder.getContext().setAuthentication(
                new UsernamePasswordAuthenticationToken(7L, null, List.of(new SimpleGrantedAuthority("ROLE_USER"))));
    }

    @AfterEach
    void tearDown() {
        SecurityContextHolder.clearContext();
    }

    @Test
    void addToWishlistWrapsResultWithoutNestedCode() throws Exception {
        when(collectionService.addToWishlistIfAbsent(7L, 7L)).thenReturn(WishlistAddResultVO.added());

        mockMvc.perform(post("/api/client/collections/7/wishlist").header("Authorization", "Bearer token"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200))
                .andExpect(jsonPath("$.message").value("success"))
                .andExpect(jsonPath("$.data.state").value("ADDED"))
                .andExpect(jsonPath("$.data.code").doesNotExist());
    }

    @Test
    void addToWishlistAlreadyCollectedCarriesExistingType() throws Exception {
        when(collectionService.addToWishlistIfAbsent(7L, 7L)).thenReturn(WishlistAddResultVO.alreadyCollected(3));

        mockMvc.perform(post("/api/client/collections/7/wishlist").header("Authorization", "Bearer token"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200))
                .andExpect(jsonPath("$.data.state").value("ALREADY_COLLECTED"))
                .andExpect(jsonPath("$.data.existingType").value(3));
    }
}
