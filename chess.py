import pygame
import sys

# --- Configuration & Constants ---
WIDTH, HEIGHT = 1000, 700
FPS = 60
BOARD_SIZE = 560
SQUARE_SIZE = BOARD_SIZE // 8
MARGIN_X = 40
MARGIN_Y = (HEIGHT - BOARD_SIZE) // 2

# Modern Color Palette
C_BG = (20, 22, 25)
C_LIGHT = (235, 236, 208)
C_DARK = (115, 149, 82)
C_HIGHLIGHT = (246, 246, 105, 150)
C_GLOW = (255, 255, 255, 50)
C_PANEL = (40, 45, 55, 200) # Glassmorphism base
C_TEXT = (240, 240, 240)
C_DANGER = (220, 50, 50, 150)

# Unicode Chess Pieces
PIECES = {
    'bR': '♜', 'bN': '♞', 'bB': '♝', 'bQ': '♛', 'bK': '♚', 'bP': '♟',
    'wR': '♖', 'wN': '♘', 'wB': '♗', 'wQ': '♕', 'wK': '♔', 'wP': '♙'
}

INITIAL_BOARD = [
    ['bR', 'bN', 'bB', 'bQ', 'bK', 'bB', 'bN', 'bR'],
    ['bP', 'bP', 'bP', 'bP', 'bP', 'bP', 'bP', 'bP'],
    ['', '', '', '', '', '', '', ''],
    ['', '', '', '', '', '', '', ''],
    ['', '', '', '', '', '', '', ''],
    ['', '', '', '', '', '', '', ''],
    ['wP', 'wP', 'wP', 'wP', 'wP', 'wP', 'wP', 'wP'],
    ['wR', 'wN', 'wB', 'wQ', 'wK', 'wB', 'wN', 'wR']
]

class ChessGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Modern Python Chess")
        self.clock = pygame.time.Clock()
        
        # Fonts
        try:
            self.piece_font = pygame.font.SysFont("segoeuisymbol", int(SQUARE_SIZE * 0.8))
        except:
            self.piece_font = pygame.font.Font(None, int(SQUARE_SIZE * 0.8))
        self.ui_font = pygame.font.SysFont("segoeui", 24)
        self.title_font = pygame.font.SysFont("segoeui", 36, bold=True)
        
        self.reset_game()

    def reset_game(self):
        self.board = [row[:] for row in INITIAL_BOARD]
        self.turn = 'w'
        self.selected_sq = None
        self.dragging = False
        self.drag_pos = (0, 0)
        self.move_history = []
        self.last_move = None
        self.check = False

    def draw_glass_panel(self, rect, radius=15):
        """Creates a semi-transparent glassmorphism panel."""
        surface = pygame.Surface((rect[2], rect[3]), pygame.SRCALPHA)
        pygame.draw.rect(surface, C_PANEL, surface.get_rect(), border_radius=radius)
        pygame.draw.rect(surface, (255, 255, 255, 30), surface.get_rect(), 2, border_radius=radius) # Border
        self.screen.blit(surface, (rect[0], rect[1]))

    def draw_board(self):
        for row in range(8):
            for col in range(8):
                color = C_LIGHT if (row + col) % 2 == 0 else C_DARK
                rect = (MARGIN_X + col * SQUARE_SIZE, MARGIN_Y + row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
                
                # Draw main squares
                pygame.draw.rect(self.screen, color, rect)
                
                # Last move highlight
                if self.last_move and (row, col) in self.last_move:
                    s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
                    s.fill(C_HIGHLIGHT)
                    self.screen.blit(s, rect[:2])

                # Selection glow
                if self.selected_sq == (row, col) and not self.dragging:
                    pygame.draw.rect(self.screen, C_HIGHLIGHT, rect, 4)

    def draw_pieces(self):
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece:
                    # Skip rendering the piece if it's currently being dragged
                    if self.dragging and self.selected_sq == (row, col):
                        continue
                        
                    text = self.piece_font.render(PIECES[piece], True, (20, 20, 20) if piece[0] == 'w' else (0, 0, 0))
                    text_rect = text.get_rect(center=(MARGIN_X + col * SQUARE_SIZE + SQUARE_SIZE//2, 
                                                      MARGIN_Y + row * SQUARE_SIZE + SQUARE_SIZE//2))
                    self.screen.blit(text, text_rect)

        # Draw dragged piece last so it's on top
        if self.dragging and self.selected_sq:
            r, c = self.selected_sq
            piece = self.board[r][c]
            if piece:
                text = self.piece_font.render(PIECES[piece], True, (20, 20, 20) if piece[0] == 'w' else (0, 0, 0))
                text_rect = text.get_rect(center=self.drag_pos)
                
                # Add a soft drop-shadow for the dragged piece
                shadow = self.piece_font.render(PIECES[piece], True, (0, 0, 0, 100))
                self.screen.blit(shadow, (text_rect.x + 5, text_rect.y + 5))
                self.screen.blit(text, text_rect)

    def draw_ui(self):
        # Top Bar Text
        title = self.title_font.render("Python Chess", True, C_TEXT)
        self.screen.blit(title, (MARGIN_X, 20))
        
        turn_text = f"{'White' if self.turn == 'w' else 'Black'}'s Turn"
        turn_surf = self.ui_font.render(turn_text, True, C_TEXT)
        self.screen.blit(turn_surf, (MARGIN_X + BOARD_SIZE - turn_surf.get_width(), 30))

        # Side Panel
        panel_x = MARGIN_X + BOARD_SIZE + 40
        panel_y = MARGIN_Y
        panel_w = WIDTH - panel_x - 40
        panel_h = BOARD_SIZE
        
        self.draw_glass_panel((panel_x, panel_y, panel_w, panel_h))
        
        # History
        hist_title = self.title_font.render("History", True, C_TEXT)
        self.screen.blit(hist_title, (panel_x + 20, panel_y + 20))
        
        y_offset = panel_y + 80
        for i, move in enumerate(self.move_history[-10:]): # Show last 10 moves
            text = self.ui_font.render(f"{len(self.move_history) - len(self.move_history[-10:]) + i + 1}. {move}", True, (200, 200, 200))
            self.screen.blit(text, (panel_x + 20, y_offset))
            y_offset += 30

        # Controls Hint
        hint = self.ui_font.render("Press 'R' to Restart", True, (150, 150, 150))
        self.screen.blit(hint, (panel_x + 20, panel_y + panel_h - 40))

    def get_square_under_mouse(self, pos):
        x, y = pos
        if MARGIN_X <= x <= MARGIN_X + BOARD_SIZE and MARGIN_Y <= y <= MARGIN_Y + BOARD_SIZE:
            col = (x - MARGIN_X) // SQUARE_SIZE
            row = (y - MARGIN_Y) // SQUARE_SIZE
            return row, col
        return None

    def execute_move(self, start_sq, end_sq):
        # Note: This is a simplified move executer (no validation engine included to keep to one file)
        # For production, integrate python-chess for move validation.
        r1, c1 = start_sq
        r2, c2 = end_sq
        piece = self.board[r1][c1]
        target = self.board[r2][c2]
        
        if piece and piece[0] == self.turn and (r1, c1) != (r2, c2):
            if target == '' or target[0] != self.turn: # Basic logic: can't capture own pieces
                self.board[r2][c2] = piece
                self.board[r1][c1] = ''
                self.last_move = (start_sq, end_sq)
                
                # Notation logic
                files = "abcdefgh"
                move_str = f"{piece[1]}{files[c1]}{8-r1} {files[c2]}{8-r2}"
                self.move_history.append(move_str)
                
                self.turn = 'b' if self.turn == 'w' else 'w'
                return True
        return False

    def run(self):
        while True:
            self.screen.fill(C_BG)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                    
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        self.reset_game()
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
                        
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1: # Left click
                        sq = self.get_square_under_mouse(event.pos)
                        if sq and self.board[sq[0]][sq[1]]:
                            self.selected_sq = sq
                            self.dragging = True
                            self.drag_pos = event.pos
                            
                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1 and self.dragging:
                        sq = self.get_square_under_mouse(event.pos)
                        if sq and self.selected_sq:
                            self.execute_move(self.selected_sq, sq)
                        self.dragging = False
                        self.selected_sq = None
                        
                elif event.type == pygame.MOUSEMOTION:
                    if self.dragging:
                        self.drag_pos = event.pos

            # Render Pipeline
            self.draw_board()
            self.draw_pieces()
            self.draw_ui()

            pygame.display.flip()
            self.clock.tick(FPS)

if __name__ == "__main__":
    game = ChessGame()
    game.run()
