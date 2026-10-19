package dev.portfolio.casepilot.tests;

import dev.portfolio.casepilot.pages.LoginPage;
import dev.portfolio.casepilot.pages.TicketsPage;
import dev.portfolio.casepilot.support.BrowserFixture;
import org.junit.jupiter.api.Test;
import java.util.UUID;
import static org.junit.jupiter.api.Assertions.*;

public class CasePilotE2ETest extends BrowserFixture {
    private static final String AGENT = "agent@casepilot.local";
    private static final String VIEWER = "viewer@casepilot.local";
    private static final String PASSWORD = "demo1234";
    private TicketsPage agent() { return new LoginPage(driver).loginAs(AGENT, PASSWORD).awaitLoaded(); }

    @Test void shouldLoginAsAgent() {
        TicketsPage page=agent();
        assertTrue(page.hasTicket("Falha ao exportar relatório"));
    }

    @Test void shouldDisplayValidationErrorOnBadCredentials() {
        LoginPage page=new LoginPage(driver);
        page.loginAs(AGENT,"invalid-password");
        assertEquals("Credenciais inválidas", page.errorMessage());
    }

    @Test void shouldCreateHighPriorityTicket() {
        TicketsPage page=agent();
        String title="Falha na impressão " + UUID.randomUUID().toString().substring(0,8);
        page.createTicket(title,"Impressora gera relatórios em branco no setor 12", "HIGH");
        assertTrue(page.hasTicket(title));
    }

    @Test void shouldBlockInvalidTitleByHtmlValidation() {
        TicketsPage page=agent();
        page.openNewTicket(); page.fillTicket("abc", "Descrição suficientemente extensa", "MEDIUM"); page.saveTicket();
        assertFalse(page.titleValidationMessage().isBlank());
    }

    @Test void shouldFilterOpenTickets() {
        TicketsPage page=agent();
        page.filter("OPEN");
        assertTrue(page.rowCount() >= 1);
        assertTrue(page.allStatusesMatch("Aberto"));
    }

    @Test void shouldSearchByTitle() {
        TicketsPage page=agent();
        page.search("exportar relatório");
        assertEquals(1, page.rowCount());
    }

    @Test void shouldUpdateTicketStatus() {
        TicketsPage page=agent();
        String title="Regressão status " + UUID.randomUUID().toString().substring(0,8);
        page.createTicket(title,"Aguardando atualização de status pelo atendente", "LOW");
        page.changeStatus(title,"IN_PROGRESS");
        assertTrue(page.hasTicket(title));
    }

    @Test void viewerMustNotHaveStatusControl() {
        TicketsPage page=new LoginPage(driver).loginAs(VIEWER,PASSWORD).awaitLoaded();
        page.createTicket("Chamado leitor " + UUID.randomUUID().toString().substring(0,8),
            "Preciso de suporte e nao posso mudar status", "MEDIUM");
        assertFalse(page.hasStatusSelector());
    }

    @Test void shouldLogout() {
        TicketsPage page=agent();
        page.logout();
        assertEquals("CasePilot — Central de Atendimento",driver.getTitle());
    }
}
