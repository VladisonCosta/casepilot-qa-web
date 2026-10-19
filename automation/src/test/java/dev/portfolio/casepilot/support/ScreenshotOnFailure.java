package dev.portfolio.casepilot.support;

import org.junit.jupiter.api.extension.AfterTestExecutionCallback;
import org.junit.jupiter.api.extension.ExtensionContext;

public class ScreenshotOnFailure implements AfterTestExecutionCallback {
    @Override
    public void afterTestExecution(ExtensionContext context) {
        if (context.getExecutionException().isPresent()
                && context.getRequiredTestInstance() instanceof BrowserFixture fixture) {
            fixture.captureFailure(context.getRequiredTestMethod().getName());
        }
    }
}
