package dev.portfolio.casepilot.pages;

import org.openqa.selenium.WebDriver;

public final class LoginPage extends BasePage {
    public LoginPage(WebDriver driver) { super(driver); }
    public TicketsPage loginAs(String email, String password) {
        visible("login-email").clear(); visible("login-email").sendKeys(email);
        visible("login-password").clear(); visible("login-password").sendKeys(password);
        clickable("login-submit").click();
        return new TicketsPage(driver);
    }
    public String errorMessage() { return visible("login-error").getText(); }
}
