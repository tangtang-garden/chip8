import pygame,sys,time,random
SCREEN_WIDTH = 64
SCREEN_HEIGHT = 32
ZOOM = 10
START_ADDR = 0x200
FONTSET_START_ADDR = 0x50
_KEYS = {
    pygame.K_1: 0x1, pygame.K_2: 0x2, pygame.K_3: 0x3, pygame.K_4: 0xC,
    pygame.K_q: 0x4, pygame.K_w: 0x5, pygame.K_e: 0x6, pygame.K_r: 0xD,
    pygame.K_a: 0x7, pygame.K_s: 0x8, pygame.K_d: 0x9, pygame.K_f: 0xE,
    pygame.K_z: 0xA, pygame.K_x: 0x0, pygame.K_c: 0xB, pygame.K_v: 0xF
}
_FONTSET = [0xF0, 0x90, 0x90, 0x90, 0xF0,  # 0
            0x20, 0x60, 0x20, 0x20, 0x70,  # 1
            0xF0, 0x10, 0xF0, 0x80, 0xF0,  # 2
            0xF0, 0x10, 0xF0, 0x10, 0xF0,  # 3
            0x90, 0x90, 0xF0, 0x10, 0x10,  # 4
            0xF0, 0x80, 0xF0, 0x10, 0xF0,  # 5
            0xF0, 0x80, 0xF0, 0x90, 0xF0,  # 6
            0xF0, 0x10, 0x20, 0x40, 0x40,  # 7
            0xF0, 0x90, 0xF0, 0x90, 0xF0,  # 8
            0xF0, 0x90, 0xF0, 0x10, 0xF0,  # 9
            0xF0, 0x90, 0xF0, 0x90, 0x90,  # A
            0xE0, 0x90, 0xE0, 0x90, 0xE0,  # B
            0xF0, 0x80, 0x80, 0x80, 0xF0,  # C
            0xE0, 0x90, 0x90, 0x90, 0xE0,  # D
            0xF0, 0x80, 0xF0, 0x80, 0xF0,  # E
            0xF0, 0x80, 0xF0, 0x80, 0x80]  # F
class Memory:
    def __init__(self) -> None:
        self.ram = [0] * 1024 * 4
        self.stack = [0] * 16
        for i in range(len(_FONTSET)):
            self.ram[FONTSET_START_ADDR+i] = _FONTSET[i]
    def write(self,data:list):
        for i in range(data):
            self.ram[START_ADDR + i] = data[i]
class Instruction:
    ...
class Display:
    ...
class Keyboard:
    ...
class CPU:
    def __init__(self) -> None:
        self.registers = [0]*16
        self.memory = Memory()
        self.regIndex = 0
        self.regPC = START_ADDR
        self.regSP = 0
        self.delayTimer = 0
        self.soundTimer = 0
        self.keypadBuf = [0]*16
        self.screenBuf = self.clearScreenBuf()
        self.opcode = 0
    def clearScreenBuf(self):
        return [[0 for i in range(SCREEN_WIDTH*ZOOM) for j in range(SCREEN_HEIGHT*ZOOM)]]
    def OP_00E0(self):
        # 00E0 CLS
        self.screenBuf = self.clearScreenBuf()
    def OP_00EE(self):
        # 00EE RET
        self.regSP -= 1
        self.regPC = self.memory.stack[self.regSP]
    def OP_1nnn(self):
        # JP addr
        addr = self.opcode & 0x0FFF
        self.regPC = addr
    def OP_2nnn(self):
        # Call addr
        addr = self.opcode & 0x0FFF
        self.memory.stack[self.regSP] = self.regPC
        self.regSP += 1
        self.regPC = addr
    def OP_3xkk(self):
        # SE vx,byte
        vx = (self.opcode & 0x0F00)>>8
        byte = self.opcode & 0x00FF
        if self.registers[vx] == byte:
            self.regPC += 2
    def OP_4xKK(self):
        # SNE vx,byte
        vx = (self.opcode & 0x0F00)>>8
        byte = self.opcode & 0x00FF
        if self.registers[vx] != byte:
            self.regPC += 2
    def OP_5xy0(self):
        # SE vx,vy
        vx = (self.opcode & 0x0F00)>>8
        vy = (self.opcode & 0x00F0)>>4
        if self.registers[vx] == self.registers[vy]:
            self.regPC += 2
    def OP_6xKK(self):
        # LD vx,byte
        vx = (self.opcode & 0x0F00) >> 8
        byte = self.opcode & 0x00FF
        self.registers[vx] = byte
    def OP_7xkk(self):
        # ADD vx,byte
        vx = (self.opcode & 0x0F00)>>8
        byte = self.opcode & 0x00FF
        self.registers[vx] += byte
    def OP_8xy0(self):
        # LD vx,vy
        vx = (self.opcode & 0x0F00)>>8
        vy = (self.opcode & 0x00F0)>>4
        self.registers[vx] = self.registers[vy]
    def OP_8xy1(self):
        # OR vx,vy
        vx = (self.opcode & 0x0F00)>>8
        vy = (self.opcode & 0x00F0)>>4
        self.registers[vx] |= self.registers[vy]
    def OP_8xy2(self):
        # AND vx,vy
        vx = (self.opcode & 0x0F00)>>8
        vy = (self.opcode & 0x00F0)>>4
        self.registers[vx] &= self.registers[vy]
    def OP_8xy3(self):
        # XOR vx,vy
        vx = (self.opcode & 0x0F00)>>8
        vy = (self.opcode & 0x00F0)>>4
        self.registers[vx] ^= self.registers[vy]
    def OP_8xy4(self):
        # ADD vx,vy
        vx = (self.opcode & 0x0F00)>>8
        vy = (self.opcode & 0x00F0)>>4
        self.registers[vx] += self.registers[vy]
        self.registers[0xF] = 1 if self.registers[vx]>0xFF else 0
        self.registers[vx] &= 0xFF
    def OP_8xy5(self):
        # SUB vx,vy
        vx = (self.opcode & 0x0F00)>>8
        vy = (self.opcode & 0x00F0)>>4
        self.registers[0xF] = 1 if self.registers[vx]>self.registers[vy] else 0
        self.registers[vx] -= self.registers[vy]
        self.registers[vx] &= 0xFF
    def OP_8xy6(self):
        # SHR vx
        vx = (self.opcode & 0x0F00)>>8
        self.registers[0xF] = self.registers[vx] & 0x1
        self.registers[vx] >>=1
    def OP_8xy7(self):
        # SUBN vx,vy
        vx = (self.opcode & 0x0F00)>>8
        vy = (self.opcode & 0x00F0)>>4
        self.registers[0xF] = 1 if self.registers[vx] > self.registers[vy] else 0
        self.registers[vx] = self.registers[vy] - self.registers[vx]
        self.registers[vx] &= 0xFF
    def OP_8xyE(self):
        # SHL vx {,vy}
        vx = (self.opcode & 0x0F00)>>8
        self.registers[0xF] = (self.registers[vx] & 0x80) >>7
        self.registers[vx] <<= 1
        self.registers[vx] &= 0xFF
    def OP_9xy0(self):
        # SNE vx,vy
        vx = (self.opcode & 0x0F00)>>8
        vy = (self.opcode & 0x00F0)>>4
        if self.registers[vx] != self.registers[vy]:
            self.regPC += 2
    def OP_Annn(self):
        # LD I,addr
        addr = self.opcode & 0x0FFF
        self.regIndex = addr
    def OP_Bnnn(self):
        # JP v0,addr
        addr = self.opcode & 0x0FFF
        self.regPC = self.registers[0] + addr
    def OP_Cxkk(self):
        # RND vx,byte
        vx = (self.opcode & 0x0F00)>>8
        byte = self.opcode & 0x00FF
        self.registers[vx] = random.randrange(0,255) & byte
    def OP_Dxyn(self):
        x = (self.opcode & 0x0F00)>>8
        y = (self.opcode & 0x00F0)>>4
        height = self.opcode & 0x000F
        vx = self.registers[x] % SCREEN_WIDTH
        vy = self.registers[y] % SCREEN_HEIGHT
        self.registers[0xF] = 0
        for row in range(height):
            spriteByte = self.memory.ram[self.regIndex + row]
            yCord = vy + row
            for col in range(8):
                xCord = vx + col
                spritePixel = spriteByte & (0x80 >> col)
                screenPixel = self.screenBuf[yPos][xPos]
                # spritePixel = (spriteByte >> (7 - col)) & 0x01   
                # screenPixel = self.screenBuf[(yPos + row)*SCREEN_WIDTH+(xPos + col)]    
        if

class Chip8:
    ...

def loadROM(filename):
    data = []
    with open(filename,'rb') as f:
        file_bytes = f.read()
        for byte in file_bytes:
            data.append(byte)
    return data


if __name__ == '__main__':
    s = loadROM('./roms/IBM')
    print(s)