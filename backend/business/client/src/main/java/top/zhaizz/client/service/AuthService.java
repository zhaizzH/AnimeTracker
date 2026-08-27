package top.zhaizz.client.service;

import top.zhaizz.client.model.IssuedAuthSession;
import top.zhaizz.pojo.dto.auth.LoginDTO;
import top.zhaizz.pojo.dto.auth.RegisterDTO;
import top.zhaizz.pojo.dto.auth.ResetPasswordDTO;

public interface AuthService {
    void register(RegisterDTO request);
    void resendCode(String email);
    IssuedAuthSession verifyEmail(String email, String code);
    IssuedAuthSession login(LoginDTO request);
    void logout(String accessToken, String refreshToken);
    IssuedAuthSession refresh(String refreshToken);
    void forgotPassword(String email);
    void resetPassword(ResetPasswordDTO request);
}