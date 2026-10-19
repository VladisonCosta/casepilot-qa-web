package dev.portfolio.casepilot.support;

import java.time.Duration;
import java.nio.file.Files;
import java.nio.file.Path;
import java.io.IOException;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.TestInfo;
import org.junit.jupiter.api.extension.ExtendWith;
import org.openqa.selenium.OutputType;
import org.openqa.selenium.TakesScreenshot;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.edge.EdgeDriver;
import org.openqa.selenium.edge.EdgeOptions;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.chrome.ChromeOptions;

@ExtendWith(ScreenshotOnFailure.class)
public abstract class BrowserFixture {
    protected WebDriver driver;
    protected final String baseUrl = System.getProperty("baseUrl", "http://localhost:8000");

    
@BeforeEach
void openBrowser() {
    String browser = System.getProperty("browser", "chrome").toLowerCase();
    boolean headless = Boolean.parseBoolean(
        System.getProperty("headless", "true")
    );

    if (browser.equals("edge")) {
        EdgeOptions opts = new EdgeOptions();
        opts.addArguments(
            "--window-size=1440,980",
            "--disable-dev-shm-usage",
            "--no-sandbox"
        );

        if (headless) {
            opts.addArguments("--headless=new");
        }

        driver = new EdgeDriver(opts);

    } else if (browser.equals("chrome")) {
        ChromeOptions opts = new ChromeOptions();
        opts.addArguments(
            "--window-size=1440,980",
            "--disable-dev-shm-usage",
            "--no-sandbox"
        );

        if (headless) {
            opts.addArguments("--headless=new");
        }

        driver = new ChromeDriver(opts);

    } else {
        throw new IllegalArgumentException(
            "Navegador não suportado: " + browser
        );
    }

    driver.manage().timeouts().pageLoadTimeout(Duration.ofSeconds(15));
    driver.get(baseUrl);
}


    @AfterEach
    void closeBrowser() {
        if (driver != null) driver.quit();
    }

    void captureFailure(String name) {
        if (driver == null) return;
        try {
            Path directory = Path.of("target", "evidence");
            Files.createDirectories(directory);
            String safe = name.replaceAll("[^a-zA-Z0-9_-]", "_");
            byte[] png = ((TakesScreenshot) driver).getScreenshotAs(OutputType.BYTES);
            Files.write(directory.resolve(safe + ".png"), png);
        } catch (IOException | org.openqa.selenium.WebDriverException e) {
            System.err.println("Screenshot unavailable: " + e.getMessage());
        }
    }
}
