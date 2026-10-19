package dev.portfolio.casepilot.pages;

import java.time.Duration;
import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;

public class BasePage {
    protected final WebDriver driver;
    protected final WebDriverWait wait;

    protected BasePage(WebDriver driver) {
        this.driver=driver;
        this.wait=new WebDriverWait(driver, Duration.ofSeconds(10));
    }
    protected By testId(String id) { return By.cssSelector("[data-testid='" + id + "']"); }
    protected WebElement visible(String id) { return wait.until(ExpectedConditions.visibilityOfElementLocated(testId(id))); }
    protected WebElement clickable(String id) { return wait.until(ExpectedConditions.elementToBeClickable(testId(id))); }
}
