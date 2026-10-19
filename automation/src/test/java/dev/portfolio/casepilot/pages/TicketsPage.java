package dev.portfolio.casepilot.pages;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.Select;

public final class TicketsPage extends BasePage {
    public TicketsPage(WebDriver driver) { super(driver); }
    public TicketsPage awaitLoaded() {
        visible("new-ticket-button");
        wait.until(d -> driver.findElement(By.id("table-footer")).getText().startsWith("Exibindo"));
        return this;
    }
    public void openNewTicket() { clickable("new-ticket-button").click(); }
    public void fillTicket(String title, String description, String priority) {
        visible("ticket-title").sendKeys(title);
        visible("ticket-description").sendKeys(description);
        new Select(visible("ticket-priority")).selectByValue(priority);
    }
    public void saveTicket() { clickable("save-ticket").click(); }
    public String titleValidationMessage() { return visible("ticket-title").getAttribute("validationMessage"); }
    public TicketsPage createTicket(String title, String description, String priority) {
        openNewTicket(); fillTicket(title, description, priority); saveTicket();
        wait.until(ExpectedConditions.invisibilityOfElementLocated(By.id("modal-backdrop")));
        wait.until(ExpectedConditions.textToBePresentInElementLocated(By.id("ticket-list"),title));
        return this;
    }
    public boolean hasTicket(String title) { return visible("ticket-list").getText().contains(title); }
    public void search(String value) {
        WebElement el=visible("search-tickets"); el.clear(); el.sendKeys(value);
        wait.until(d -> {
            java.util.List<WebElement> rows=driver.findElements(testId("ticket-row"));
            return !rows.isEmpty() && rows.stream().allMatch(r -> r.getText().toLowerCase().contains(value.toLowerCase()));
        });
    }
    public void filter(String status) {
        new Select(visible("filter-status")).selectByValue(status);
        String expected = switch(status) { case "OPEN" -> "Aberto"; case "IN_PROGRESS" -> "Em andamento"; case "RESOLVED" -> "Resolvido"; default -> ""; };
        wait.ignoring(org.openqa.selenium.StaleElementReferenceException.class)
    .until(d -> {
            java.util.List<WebElement> rows=driver.findElements(testId("ticket-status"));
            return !rows.isEmpty() && rows.stream().allMatch(el -> expected.isEmpty() || el.getText().equals(expected));
        });
    }
    public long rowCount() { return driver.findElements(testId("ticket-row")).size(); }
    public boolean allStatusesMatch(String statusText) {
        return driver.findElements(testId("ticket-status")).stream().allMatch(element -> element.getText().equals(statusText));
    }
    public void changeStatus(String title, String toStatus) {
        WebElement row=driver.findElements(testId("ticket-row")).stream()
             .filter(e -> e.getText().contains(title)).findFirst().orElseThrow();
        new Select(row.findElement(testId("status-change"))).selectByValue(toStatus);
        wait.ignoring(org.openqa.selenium.StaleElementReferenceException.class)
    .until(d -> driver.findElements(testId("ticket-row")).stream().anyMatch(e ->
          e.getText().contains(title) && e.findElement(testId("ticket-status")).getText().equals(
              switch(toStatus){case "OPEN" -> "Aberto";case "IN_PROGRESS" -> "Em andamento";default -> "Resolvido";})));
    }
    public boolean hasStatusSelector() { return !driver.findElements(testId("status-change")).isEmpty(); }
    public void logout() { clickable("logout-button").click(); wait.until(ExpectedConditions.visibilityOfElementLocated(testId("login-submit"))); }
}
