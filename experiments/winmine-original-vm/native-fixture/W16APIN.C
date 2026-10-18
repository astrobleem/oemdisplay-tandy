#define WINVER 0x0300
#include <windows.h>

#define LOG_PATH "C:\\W16API.LOG"
#define CALLBACK_COOKIE 0x13579BDFL
#define LOG_LIMIT 64
#define VM_STACK_WORDS 8
#define VM_STEP_LIMIT 64
#define VM_IMPORT_GETVERSION 1
#define VM_CODE_SELECTOR 0x1000
#define VM_IMPORT_SELECTOR 0xF001
#define VM_IMPORT_GETVERSION_OFFSET 0x0001

#define VM_AX 0
#define VM_CX 1
#define VM_DX 2
#define VM_BX 3
#define VM_SP 4
#define VM_BP 5
#define VM_SI 6
#define VM_DI 7

#define VM_ERR_NONE 0
#define VM_ERR_BOUNDS 1
#define VM_ERR_STACK 2
#define VM_ERR_MODRM 3
#define VM_ERR_BRANCH 4
#define VM_ERR_IMPORT 5
#define VM_ERR_OPCODE 6
#define VM_ERR_LIMIT 7

/* MOV AX,GetVersion; INT FF import; HLT. The bridge calls real Win16 GetVersion. */
static const BYTE g_version_bytecode[] = {
    0xB8, 0x01, 0x00, 0xCD, 0xFF, 0xF4
};

/* CALL FAR through the VM import table, then resume at HLT. */
static const BYTE g_farcall_version_bytecode[] = {
    0x9A, 0x01, 0x00, 0x01, 0xF0, 0xF4
};

/*
 * 8088 callback bytecode. POP AX/BX/CX/DX reads HWND, LPARAM low/high,
 * and stop-mode from the virtual stack. It returns TRUE only for a nonzero
 * HWND, the expected cookie, and all-pass mode. Unsupported opcodes fail closed.
 */
static const BYTE g_callback_bytecode[] = {
    0x58,                         /* POP AX (HWND) */
    0x5B,                         /* POP BX (LPARAM low) */
    0x59,                         /* POP CX (LPARAM high) */
    0x5A,                         /* POP DX (stop mode) */
    0x81, 0xF8, 0x00, 0x00,       /* CMP AX, 0 */
    0x74, 0x16,                   /* JZ return_false */
    0x81, 0xFB, 0xDF, 0x9B,       /* CMP BX, 0x9BDF */
    0x75, 0x10,                   /* JNZ return_false */
    0x81, 0xF9, 0x57, 0x13,       /* CMP CX, 0x1357 */
    0x75, 0x0A,                   /* JNZ return_false */
    0x81, 0xFA, 0x00, 0x00,       /* CMP DX, 0 (all-pass mode) */
    0x75, 0x04,                   /* JNZ return_false */
    0xB8, 0x01, 0x00,             /* MOV AX, TRUE */
    0xF4,                         /* HLT */
    0xB8, 0x00, 0x00,             /* return_false: MOV AX, FALSE */
    0xF4                          /* HLT */
};

/*
 * Minimal assembled 8088 Pascal callback: CALL FAR 1000:0006, then HLT.
 * The callback reads [BP+10]=HWND, [BP+6]/[BP+8]=LPARAM low/high, checks
 * CX=stop mode, and returns with RETF 6 to model callee argument cleanup.
 */
static const BYTE g_far_callback_bytecode[] = {
    0x9A, 0x06, 0x00, 0x00, 0x10, 0xF4,
    0x55,                         /* callback: PUSH BP */
    0x8B, 0xEC,                   /* MOV BP, SP */
    0x83, 0x7E, 0x0A, 0x00,       /* CMP WORD PTR [BP+10], 0 (HWND) */
    0x74, 0x1A,                   /* JZ return_false */
    0x81, 0x7E, 0x06, 0xDF, 0x9B, /* CMP WORD PTR [BP+6], 0x9BDF */
    0x75, 0x13,                   /* JNZ return_false */
    0x81, 0x7E, 0x08, 0x57, 0x13, /* CMP WORD PTR [BP+8], 0x1357 */
    0x75, 0x0C,                   /* JNZ return_false */
    0x83, 0xF9, 0x00,             /* CMP CX, 0 (all-pass mode) */
    0x75, 0x07,                   /* JNZ return_false */
    0xB8, 0x01, 0x00,             /* MOV AX, TRUE */
    0x5D,                         /* POP BP */
    0xCA, 0x06, 0x00,             /* RETF 6 */
    0xB8, 0x00, 0x00,             /* return_false: MOV AX, FALSE */
    0x5D,                         /* POP BP */
    0xCA, 0x06, 0x00              /* RETF 6 */
};

static const BYTE g_unsupported_bytecode[] = { 0x90 }; /* NOP is outside this subset. */

typedef struct {
    WORD reg[8];
    WORD stack[VM_STACK_WORDS];
    WORD cs;
    WORD ip;
    WORD steps;
    WORD error_ip;
    WORD far_calls;
    WORD far_returns;
    WORD last_return_cs;
    WORD last_return_ip;
    WORD last_retf_bytes;
    BYTE zero_flag;
    BYTE error;
    BYTE error_opcode;
} VM8088;

static HFILE g_log = (HFILE)-1;
static HWND g_probe_window = (HWND)0;
static unsigned g_all_count = 0;
static unsigned g_logged_count = 0;
static unsigned g_stop_count = 0;
static int g_cookie_ok = 1;
static int g_probe_seen = 0;
static int g_stop_mode = 0;
static unsigned g_vm_callback_invocations = 0;
static unsigned g_vm_getversion_calls = 0;
static unsigned g_vm_far_getversion_calls = 0;
static unsigned g_vm_failures = 0;

static void put_text(const char FAR *text)
{
    if (g_log != (HFILE)-1 && text != (const char FAR *)0)
        _lwrite(g_log, (const void _huge *)text, (UINT)lstrlen(text));
}

static void put_hex(unsigned long value, unsigned digits)
{
    static const char hex[] = "0123456789ABCDEF";
    char buffer[8];
    unsigned i;

    for (i = 0; i < digits; ++i) {
        buffer[digits - i - 1] = hex[(unsigned)(value & 0x0F)];
        value >>= 4;
    }
    _lwrite(g_log, (const void _huge *)buffer, (UINT)digits);
}

static void put_decimal(unsigned value)
{
    char buffer[6];
    unsigned used = 0;

    do {
        buffer[used++] = (char)('0' + (value % 10));
        value /= 10;
    } while (value != 0 && used < sizeof(buffer));
    while (used != 0) {
        --used;
        _lwrite(g_log, (const void _huge *)&buffer[used], 1);
    }
}

static void put_newline(void)
{
    put_text("\r\n");
}

static void log_window(const char FAR *tag, HWND hwnd, LPARAM cookie)
{
    put_text(tag);
    put_text(" hwnd=0x");
    put_hex((unsigned long)(WORD)hwnd, 4);
    put_text(" lParam=0x");
    put_hex((unsigned long)cookie, 8);
    put_newline();
}

static void vm_init(VM8088 *vm)
{
    unsigned i;

    for (i = 0; i < 8; ++i)
        vm->reg[i] = 0;
    for (i = 0; i < VM_STACK_WORDS; ++i)
        vm->stack[i] = 0;
    vm->reg[VM_SP] = VM_STACK_WORDS;
    vm->cs = VM_CODE_SELECTOR;
    vm->ip = 0;
    vm->steps = 0;
    vm->error_ip = 0;
    vm->far_calls = 0;
    vm->far_returns = 0;
    vm->last_return_cs = 0;
    vm->last_return_ip = 0;
    vm->last_retf_bytes = 0;
    vm->zero_flag = 0;
    vm->error = VM_ERR_NONE;
    vm->error_opcode = 0;
}

static int vm_fetch8(VM8088 *vm, const BYTE *program, unsigned program_size,
                     BYTE *value)
{
    if (vm->cs != VM_CODE_SELECTOR || vm->ip >= program_size) {
        vm->error = VM_ERR_BOUNDS;
        vm->error_ip = vm->ip;
        return 0;
    }
    *value = program[vm->ip++];
    return 1;
}

static int vm_fetch16(VM8088 *vm, const BYTE *program, unsigned program_size,
                      WORD *value)
{
    BYTE low;
    BYTE high;

    if (!vm_fetch8(vm, program, program_size, &low) ||
        !vm_fetch8(vm, program, program_size, &high))
        return 0;
    *value = (WORD)(((WORD)high << 8) | low);
    return 1;
}

static int vm_push16(VM8088 *vm, WORD value)
{
    WORD sp = vm->reg[VM_SP];

    if (sp == 0 || sp > VM_STACK_WORDS) {
        vm->error = VM_ERR_STACK;
        return 0;
    }
    --sp;
    vm->stack[sp] = value;
    vm->reg[VM_SP] = sp;
    return 1;
}

static int vm_pop16(VM8088 *vm, WORD *value)
{
    WORD sp = vm->reg[VM_SP];

    if (sp >= VM_STACK_WORDS) {
        vm->error = VM_ERR_STACK;
        return 0;
    }
    *value = vm->stack[sp];
    vm->reg[VM_SP] = (WORD)(sp + 1);
    return 1;
}

static int vm_call_far(VM8088 *vm, WORD selector, WORD offset)
{
    if (!vm_push16(vm, vm->cs) || !vm_push16(vm, vm->ip))
        return 0;
    ++vm->far_calls;
    vm->cs = selector;
    vm->ip = offset;
    return 1;
}

static int vm_retf(VM8088 *vm, WORD argument_bytes)
{
    WORD return_ip;
    WORD return_cs;
    WORD sp;

    if (argument_bytes & 1) {
        vm->error = VM_ERR_STACK;
        return 0;
    }
    if (!vm_pop16(vm, &return_ip) || !vm_pop16(vm, &return_cs))
        return 0;
    sp = vm->reg[VM_SP];
    if ((unsigned)sp + argument_bytes / 2 > VM_STACK_WORDS) {
        vm->error = VM_ERR_STACK;
        return 0;
    }
    vm->reg[VM_SP] = (WORD)(sp + argument_bytes / 2);
    vm->last_return_cs = return_cs;
    vm->last_return_ip = return_ip;
    vm->last_retf_bytes = argument_bytes;
    ++vm->far_returns;
    vm->cs = return_cs;
    vm->ip = return_ip;
    return 1;
}

static int vm_read_bp_word(VM8088 *vm, BYTE displacement, WORD *value)
{
    unsigned stack_index;

    if (displacement >= 0x80 || (displacement & 1)) {
        vm->error = VM_ERR_MODRM;
        return 0;
    }
    stack_index = (unsigned)vm->reg[VM_BP] + (unsigned)(displacement / 2);
    if (stack_index >= VM_STACK_WORDS) {
        vm->error = VM_ERR_STACK;
        return 0;
    }
    *value = vm->stack[stack_index];
    return 1;
}

/* INT FF is the only software bridge. Only the real imported GetVersion API exists. */
static int vm_import_dispatch(VM8088 *vm)
{
    DWORD version;

    if (vm->reg[VM_AX] != VM_IMPORT_GETVERSION) {
        vm->error = VM_ERR_IMPORT;
        return 0;
    }
    version = GetVersion();
    vm->reg[VM_AX] = (WORD)(version & 0xFFFFUL);
    vm->reg[VM_DX] = (WORD)((version >> 16) & 0xFFFFUL);
    ++g_vm_getversion_calls;
    return 1;
}

/* Resolve one far-import token to the real imported Win16 GetVersion API. */
static int vm_far_import_dispatch(VM8088 *vm)
{
    DWORD version;

    if (vm->cs != VM_IMPORT_SELECTOR ||
        vm->ip != VM_IMPORT_GETVERSION_OFFSET) {
        vm->error = VM_ERR_IMPORT;
        return 0;
    }
    version = GetVersion();
    vm->reg[VM_AX] = (WORD)(version & 0xFFFFUL);
    vm->reg[VM_DX] = (WORD)((version >> 16) & 0xFFFFUL);
    ++g_vm_far_getversion_calls;
    return vm_retf(vm, 0);
}

/*
 * Bounded 8088 subset: PUSH/POP BP/register, MOV r16,imm16, MOV BP,SP,
 * register or BP+disp8 CMP /7 (81/83), short JZ/JNZ, CALL FAR, INT FF baseline,
 * RETF/RETF imm16, and HLT. Unsupported forms fail closed.
 */
static int vm_run(VM8088 *vm, const BYTE *program, unsigned program_size)
{
    unsigned step;
    BYTE opcode;
    BYTE modrm;
    BYTE value;
    WORD immediate;
    WORD popped;
    WORD compared;
    WORD return_bytes;
    unsigned reg_index;
    unsigned mod;
    int target;
    int take_branch;

    vm->steps = 0;
    for (step = 0; step < VM_STEP_LIMIT; ++step) {
        vm->error_ip = vm->ip;
        vm->error_opcode = 0x9A;
        vm->steps = (WORD)(step + 1);
        if (vm->cs == VM_IMPORT_SELECTOR) {
            if (!vm_far_import_dispatch(vm))
                return 0;
            continue;
        }
        if (vm->cs != VM_CODE_SELECTOR) {
            vm->error = VM_ERR_IMPORT;
            return 0;
        }
        if (!vm_fetch8(vm, program, program_size, &opcode))
            return 0;
        vm->error_opcode = opcode;

        if (opcode >= 0x58 && opcode <= 0x5F) {
            reg_index = (unsigned)(opcode - 0x58);
            if (reg_index == VM_SP || !vm_pop16(vm, &popped)) {
                vm->error = VM_ERR_STACK;
                return 0;
            }
            vm->reg[reg_index] = popped;
        } else if (opcode >= 0xB8 && opcode <= 0xBF) {
            reg_index = (unsigned)(opcode - 0xB8);
            if (reg_index == VM_SP) {
                vm->error = VM_ERR_STACK;
                return 0;
            }
            if (!vm_fetch16(vm, program, program_size, &immediate))
                return 0;
            vm->reg[reg_index] = immediate;
        } else if (opcode == 0x55) {
            if (!vm_push16(vm, vm->reg[VM_BP]))
                return 0;
        } else if (opcode == 0x89 || opcode == 0x8B) {
            if (!vm_fetch8(vm, program, program_size, &modrm))
                return 0;
            if ((opcode == 0x89 && modrm != 0xE5) ||
                (opcode == 0x8B && modrm != 0xEC)) {
                vm->error = VM_ERR_MODRM;
                return 0;
            }
            vm->reg[VM_BP] = vm->reg[VM_SP];
        } else if (opcode == 0x81 || opcode == 0x83) {
            if (!vm_fetch8(vm, program, program_size, &modrm))
                return 0;
            mod = (unsigned)(modrm >> 6);
            if (((modrm >> 3) & 7) != 7) {
                vm->error = VM_ERR_MODRM;
                return 0;
            }
            if (mod == 3) {
                reg_index = modrm & 7;
                compared = vm->reg[reg_index];
            } else if (mod == 1 && (modrm & 7) == 6) {
                if (!vm_fetch8(vm, program, program_size, &value) ||
                    !vm_read_bp_word(vm, value, &compared))
                    return 0;
            } else {
                vm->error = VM_ERR_MODRM;
                return 0;
            }
            if (opcode == 0x81) {
                if (!vm_fetch16(vm, program, program_size, &immediate))
                    return 0;
            } else {
                if (!vm_fetch8(vm, program, program_size, &value))
                    return 0;
                immediate = value < 0x80 ? value : (WORD)(0xFF00 | value);
            }
            vm->zero_flag = (BYTE)(compared == immediate);
        } else if (opcode == 0x74 || opcode == 0x75) {
            if (!vm_fetch8(vm, program, program_size, &value))
                return 0;
            take_branch = opcode == 0x74 ? vm->zero_flag : !vm->zero_flag;
            if (take_branch) {
                target = (int)vm->ip;
                if (value < 0x80)
                    target += value;
                else
                    target -= (int)(0x100 - value);
                if (target < 0 || target >= (int)program_size) {
                    vm->error = VM_ERR_BRANCH;
                    return 0;
                }
                vm->ip = (WORD)target;
            }
        } else if (opcode == 0x9A) {
            WORD target_offset;
            WORD target_selector;

            if (!vm_fetch16(vm, program, program_size, &target_offset) ||
                !vm_fetch16(vm, program, program_size, &target_selector))
                return 0;
            if (!vm_call_far(vm, target_selector, target_offset))
                return 0;
        } else if (opcode == 0xCD) {
            if (!vm_fetch8(vm, program, program_size, &value))
                return 0;
            if (value != 0xFF || !vm_import_dispatch(vm)) {
                if (vm->error == VM_ERR_NONE)
                    vm->error = VM_ERR_IMPORT;
                return 0;
            }
        } else if (opcode == 0xCA || opcode == 0xCB) {
            return_bytes = 0;
            if (opcode == 0xCA &&
                !vm_fetch16(vm, program, program_size, &return_bytes))
                return 0;
            if (!vm_retf(vm, return_bytes))
                return 0;
        } else if (opcode == 0xF4) {
            return 1;
        } else {
            vm->error = VM_ERR_OPCODE;
            return 0;
        }
    }
    vm->error = VM_ERR_LIMIT;
    vm->error_ip = vm->ip;
    vm->steps = VM_STEP_LIMIT;
    return 0;
}

static const char *vm_error_name(BYTE error)
{
    switch (error) {
    case VM_ERR_BOUNDS: return "bounds";
    case VM_ERR_STACK: return "stack";
    case VM_ERR_MODRM: return "modrm";
    case VM_ERR_BRANCH: return "branch";
    case VM_ERR_IMPORT: return "import";
    case VM_ERR_OPCODE: return "opcode";
    case VM_ERR_LIMIT: return "limit";
    default: return "none";
    }
}

static BOOL vm_getversion(DWORD *version, WORD *steps,
                          BYTE *error, BYTE *bad_opcode, WORD *error_ip)
{
    VM8088 vm;

    vm_init(&vm);
    if (!vm_run(&vm, g_version_bytecode, sizeof(g_version_bytecode))) {
        *error = vm.error;
        *bad_opcode = vm.error_opcode;
        *error_ip = vm.error_ip;
        return FALSE;
    }
    if (vm.reg[VM_SP] != VM_STACK_WORDS) {
        *error = VM_ERR_STACK;
        *bad_opcode = 0;
        *error_ip = vm.ip;
        return FALSE;
    }
    *version = ((DWORD)vm.reg[VM_DX] << 16) | vm.reg[VM_AX];
    *steps = vm.steps;
    *error = VM_ERR_NONE;
    *bad_opcode = 0;
    *error_ip = 0;
    return TRUE;
}

static BOOL vm_getversion_far(DWORD *version, WORD *steps, WORD *final_sp,
                              WORD *far_calls, WORD *far_returns,
                              WORD *return_cs, WORD *return_ip,
                              WORD *retf_bytes, BYTE *error,
                              BYTE *bad_opcode, WORD *error_ip)
{
    VM8088 vm;

    vm_init(&vm);
    if (!vm_run(&vm, g_farcall_version_bytecode,
                sizeof(g_farcall_version_bytecode))) {
        *error = vm.error;
        *bad_opcode = vm.error_opcode;
        *error_ip = vm.error_ip;
        *final_sp = vm.reg[VM_SP];
        return FALSE;
    }
    *final_sp = vm.reg[VM_SP];
    *far_calls = vm.far_calls;
    *far_returns = vm.far_returns;
    *return_cs = vm.last_return_cs;
    *return_ip = vm.last_return_ip;
    *retf_bytes = vm.last_retf_bytes;
    if (vm.reg[VM_SP] != VM_STACK_WORDS || vm.cs != VM_CODE_SELECTOR ||
        vm.ip != sizeof(g_farcall_version_bytecode) ||
        vm.far_calls != 1 || vm.far_returns != 1 ||
        vm.last_return_cs != VM_CODE_SELECTOR || vm.last_return_ip != 5 ||
        vm.last_retf_bytes != 0) {
        *error = VM_ERR_STACK;
        *bad_opcode = 0;
        *error_ip = vm.ip;
        return FALSE;
    }
    *version = ((DWORD)vm.reg[VM_DX] << 16) | vm.reg[VM_AX];
    *steps = vm.steps;
    *error = VM_ERR_NONE;
    *bad_opcode = 0;
    *error_ip = 0;
    return TRUE;
}

static BOOL vm_callback_result(HWND hwnd, LPARAM cookie, int stop_mode,
                               WORD *result, WORD *steps, WORD *final_sp,
                               BYTE *error, BYTE *bad_opcode, WORD *error_ip)
{
    VM8088 vm;
    DWORD cookie_bits = (DWORD)cookie;

    vm_init(&vm);
    if (!vm_push16(&vm, (WORD)stop_mode) ||
        !vm_push16(&vm, (WORD)((cookie_bits >> 16) & 0xFFFFUL)) ||
        !vm_push16(&vm, (WORD)(cookie_bits & 0xFFFFUL)) ||
        !vm_push16(&vm, (WORD)hwnd) ||
        !vm_run(&vm, g_callback_bytecode, sizeof(g_callback_bytecode))) {
        *error = vm.error;
        *bad_opcode = vm.error_opcode;
        *error_ip = vm.error_ip;
        *final_sp = vm.reg[VM_SP];
        return FALSE;
    }
    *final_sp = vm.reg[VM_SP];
    if (*final_sp != VM_STACK_WORDS) {
        *error = VM_ERR_STACK;
        *bad_opcode = 0;
        *error_ip = vm.ip;
        return FALSE;
    }
    *result = vm.reg[VM_AX];
    *steps = vm.steps;
    *error = VM_ERR_NONE;
    *bad_opcode = 0;
    *error_ip = 0;
    return TRUE;
}

static BOOL vm_callback_far_result(HWND hwnd, LPARAM cookie, int stop_mode,
                                   WORD *result, WORD *steps, WORD *final_sp,
                                   WORD *far_calls, WORD *far_returns,
                                   WORD *retf_bytes, WORD *return_cs,
                                   WORD *return_ip, WORD *final_bp,
                                   BYTE *error, BYTE *bad_opcode, WORD *error_ip)
{
    VM8088 vm;
    DWORD cookie_bits = (DWORD)cookie;

    vm_init(&vm);
    vm.reg[VM_CX] = (WORD)stop_mode;
    /* Win16 Pascal order: HWND, then LPARAM high word, then LPARAM low word. */
    if (!vm_push16(&vm, (WORD)hwnd) ||
        !vm_push16(&vm, (WORD)((cookie_bits >> 16) & 0xFFFFUL)) ||
        !vm_push16(&vm, (WORD)(cookie_bits & 0xFFFFUL)) ||
        !vm_run(&vm, g_far_callback_bytecode,
                sizeof(g_far_callback_bytecode))) {
        *error = vm.error;
        *bad_opcode = vm.error_opcode;
        *error_ip = vm.error_ip;
        *final_sp = vm.reg[VM_SP];
        return FALSE;
    }
    *final_sp = vm.reg[VM_SP];
    *far_calls = vm.far_calls;
    *far_returns = vm.far_returns;
    *retf_bytes = vm.last_retf_bytes;
    *return_cs = vm.last_return_cs;
    *return_ip = vm.last_return_ip;
    *final_bp = vm.reg[VM_BP];
    if (*final_sp != VM_STACK_WORDS || vm.cs != VM_CODE_SELECTOR ||
        vm.ip != 6 || *far_calls != 1 || *far_returns != 1 ||
        *retf_bytes != 6 || *return_cs != VM_CODE_SELECTOR ||
        *return_ip != 5 || *final_bp != 0) {
        *error = VM_ERR_STACK;
        *bad_opcode = 0;
        *error_ip = vm.ip;
        return FALSE;
    }
    *result = vm.reg[VM_AX];
    *steps = vm.steps;
    *error = VM_ERR_NONE;
    *bad_opcode = 0;
    *error_ip = 0;
    return TRUE;
}

static BOOL vm_cookie_selftest(WORD *steps, WORD *final_sp)
{
    WORD result;
    BYTE error;
    BYTE bad_opcode;
    WORD error_ip;

    if (!vm_callback_result((HWND)0x2468,
                            (LPARAM)(CALLBACK_COOKIE ^ 1L), 0,
                            &result, steps, final_sp,
                            &error, &bad_opcode, &error_ip))
        return FALSE;
    return result == 0 && *final_sp == VM_STACK_WORDS;
}

static BOOL vm_smoke_callback_selftest(WORD *steps, WORD *final_sp)
{
    WORD result;
    BYTE error;
    BYTE bad_opcode;
    WORD error_ip;

    if (!vm_callback_result((HWND)0x2468, (LPARAM)CALLBACK_COOKIE, 0,
                            &result, steps, final_sp,
                            &error, &bad_opcode, &error_ip))
        return FALSE;
    return result == 1 && *final_sp == VM_STACK_WORDS;
}

static BOOL vm_far_cookie_selftest(WORD *steps, WORD *final_sp,
                                   WORD *return_cs, WORD *return_ip,
                                   WORD *retf_bytes)
{
    WORD result;
    WORD far_calls;
    WORD far_returns;
    WORD final_bp;
    BYTE error;
    BYTE bad_opcode;
    WORD error_ip;

    if (!vm_callback_far_result((HWND)0x2468,
                                (LPARAM)(CALLBACK_COOKIE ^ 1L), 0,
                                &result, steps, final_sp,
                                &far_calls, &far_returns, retf_bytes,
                                return_cs, return_ip, &final_bp,
                                &error, &bad_opcode, &error_ip))
        return FALSE;
    return result == 0 && *final_sp == VM_STACK_WORDS &&
           far_calls == 1 && far_returns == 1 && final_bp == 0;
}

static BOOL vm_unsupported_selftest(void)
{
    VM8088 vm;

    vm_init(&vm);
    if (vm_run(&vm, g_unsupported_bytecode, sizeof(g_unsupported_bytecode)))
        return FALSE;
    return vm.error == VM_ERR_OPCODE && vm.error_opcode == 0x90;
}

static BOOL vm_unknown_far_import_selftest(void)
{
    static const BYTE unknown_import[] = {
        0x9A, 0x02, 0x00, 0x01, 0xF0, 0xF4
    };
    VM8088 vm;

    vm_init(&vm);
    if (vm_run(&vm, unknown_import, sizeof(unknown_import)))
        return FALSE;
    return vm.error == VM_ERR_IMPORT && vm.error_opcode == 0x9A;
}

static void log_vm_result(WORD result, WORD steps, WORD final_sp)
{
    put_text("VM callback result=");
    put_decimal(result);
    put_text(" stack=");
    put_decimal(final_sp == VM_STACK_WORDS ? 1 : 0);
    put_text(" steps=");
    put_decimal(steps);
    put_newline();
}

static void log_vm_far_result(WORD result, WORD steps, WORD final_sp,
                              WORD far_calls, WORD far_returns,
                              WORD retf_bytes, WORD return_cs, WORD return_ip)
{
    put_text("VM guest callback result=");
    put_decimal(result);
    put_text(" stack=");
    put_decimal(final_sp == VM_STACK_WORDS ? 1 : 0);
    put_text(" steps=");
    put_decimal(steps);
    put_text(" far_calls=");
    put_decimal(far_calls);
    put_text(" retf=");
    put_decimal(far_returns);
    put_text(" retf_bytes=");
    put_decimal(retf_bytes);
    put_text(" return=");
    put_hex(return_cs, 4);
    put_text(":");
    put_hex(return_ip, 4);
    put_newline();
}

BOOL FAR PASCAL EnumProc(HWND hwnd, LPARAM cookie)
{
    WORD result = 0;
    WORD steps = 0;
    WORD final_sp = 0;
    WORD far_calls = 0;
    WORD far_returns = 0;
    WORD retf_bytes = 0;
    WORD return_cs = 0;
    WORD return_ip = 0;
    WORD final_bp = 0;
    BYTE error = VM_ERR_NONE;
    BYTE bad_opcode = 0;
    WORD error_ip = 0;

    ++g_vm_callback_invocations;
    if (!vm_callback_far_result(hwnd, cookie, g_stop_mode,
                                &result, &steps, &final_sp,
                                &far_calls, &far_returns, &retf_bytes,
                                &return_cs, &return_ip, &final_bp,
                                &error, &bad_opcode, &error_ip)) {
        ++g_vm_failures;
        log_window("FAIL VM callback", hwnd, cookie);
        put_text("VM error=");
        put_text(vm_error_name(error));
        put_text(" opcode=0x");
        put_hex(bad_opcode, 2);
        put_text(" ip=0x");
        put_hex(error_ip, 4);
        put_text(" sp=0x");
        put_hex(final_sp, 4);
        put_newline();
        return FALSE;
    }

    if (g_stop_mode) {
        ++g_stop_count;
        if (g_stop_count <= LOG_LIMIT)
            log_window("STOP callback", hwnd, cookie);
        log_vm_far_result(result, steps, final_sp, far_calls, far_returns,
                          retf_bytes, return_cs, return_ip);
        return (BOOL)result;
    }

    ++g_all_count;
    if (cookie != (LPARAM)CALLBACK_COOKIE)
        g_cookie_ok = 0;
    if (hwnd == g_probe_window)
        g_probe_seen = 1;
    if (g_logged_count < LOG_LIMIT) {
        log_window("ENUM callback", hwnd, cookie);
        log_vm_far_result(result, steps, final_sp, far_calls, far_returns,
                          retf_bytes, return_cs, return_ip);
        ++g_logged_count;
    }
    return (BOOL)result;
}

int PASCAL WinMain(HINSTANCE instance, HINSTANCE previous,
                   LPSTR command_line, int show_command)
{
    DWORD version;
    DWORD smoke_version;
    WORD low_version;
    WORD vm_steps = 0;
    WORD vm_final_sp = 0;
    WORD far_calls = 0;
    WORD far_returns = 0;
    WORD retf_bytes = 0;
    WORD return_cs = 0;
    WORD return_ip = 0;
    BYTE vm_error = VM_ERR_NONE;
    BYTE vm_bad_opcode = 0;
    WORD vm_error_ip = 0;
    FARPROC thunk;
    BOOL enum_result;
    int failures = 0;

    (void)previous;
    (void)command_line;
    (void)show_command;

    g_log = _lcreat(LOG_PATH, 0);
    if (g_log == (HFILE)-1)
        return 2;

    put_text("Native Win16 API fixture\r\n");
    if (!vm_getversion(&smoke_version, &vm_steps,
                       &vm_error, &vm_bad_opcode, &vm_error_ip)) {
        put_text("FAIL VM smoke GetVersion error=");
        put_text(vm_error_name(vm_error));
        put_text(" opcode=0x");
        put_hex(vm_bad_opcode, 2);
        put_text(" ip=0x");
        put_hex(vm_error_ip, 4);
        put_newline();
        failures = 1;
        smoke_version = 0;
    } else {
        put_text("VM smoke GetVersion INTFF=PASS calls=");
        put_decimal(g_vm_getversion_calls);
        put_text(" steps=");
        put_decimal(vm_steps);
        put_text(" stack=");
        put_decimal(VM_STACK_WORDS);
        put_newline();
    }
    if (g_vm_getversion_calls != 1)
        failures = 1;

    vm_steps = 0;
    vm_final_sp = 0;
    if (!vm_getversion_far(&version, &vm_steps, &vm_final_sp,
                           &far_calls, &far_returns, &return_cs, &return_ip,
                           &retf_bytes, &vm_error, &vm_bad_opcode,
                           &vm_error_ip)) {
        put_text("FAIL VM far GetVersion error=");
        put_text(vm_error_name(vm_error));
        put_text(" opcode=0x");
        put_hex(vm_bad_opcode, 2);
        put_text(" ip=0x");
        put_hex(vm_error_ip, 4);
        put_newline();
        failures = 1;
        version = 0;
    } else {
        put_text("VM far GetVersion CALL=PASS calls=");
        put_decimal(g_vm_far_getversion_calls);
        put_text(" steps=");
        put_decimal(vm_steps);
        put_text(" far_calls=");
        put_decimal(far_calls);
        put_text(" retf=");
        put_decimal(far_returns);
        put_text(" retf_bytes=");
        put_decimal(retf_bytes);
        put_text(" return=");
        put_hex(return_cs, 4);
        put_text(":");
        put_hex(return_ip, 4);
        put_text(" stack=");
        put_decimal(vm_final_sp == VM_STACK_WORDS ? 1 : 0);
        put_newline();
    }
    if (g_vm_far_getversion_calls != 1 || version != smoke_version)
        failures = 1;
    put_text("GetVersion DWORD=0x");
    put_hex(version, 8);
    put_newline();
    low_version = (WORD)(version & 0xFFFFL);
    put_text("Windows version major=");
    put_decimal((unsigned)(low_version & 0x00FF));
    put_text(" minor=");
    put_decimal((unsigned)((low_version >> 8) & 0x00FF));
    put_newline();

    vm_steps = 0;
    vm_final_sp = 0;
    if (!vm_smoke_callback_selftest(&vm_steps, &vm_final_sp)) {
        put_text("FAIL VM smoke callback selftest\r\n");
        failures = 1;
    } else {
        put_text("VM smoke callback result=1 stack=1 steps=");
        put_decimal(vm_steps);
        put_newline();
    }
    vm_steps = 0;
    vm_final_sp = 0;
    if (!vm_cookie_selftest(&vm_steps, &vm_final_sp)) {
        put_text("FAIL VM smoke wrong-cookie selftest\r\n");
        failures = 1;
    } else {
        put_text("VM smoke wrong-cookie result=0 stack=1 steps=");
        put_decimal(vm_steps);
        put_newline();
    }
    vm_steps = 0;
    vm_final_sp = 0;
    if (!vm_far_cookie_selftest(&vm_steps, &vm_final_sp,
                                &return_cs, &return_ip, &retf_bytes)) {
        put_text("FAIL VM far wrong-cookie selftest\r\n");
        failures = 1;
    } else {
        put_text("VM far wrong-cookie result=0 stack=1 retf=1 bytes=");
        put_decimal(retf_bytes);
        put_text(" return=");
        put_hex(return_cs, 4);
        put_text(":");
        put_hex(return_ip, 4);
        put_newline();
    }
    if (!vm_unsupported_selftest()) {
        put_text("FAIL VM unsupported opcode was not rejected\r\n");
        failures = 1;
    } else {
        put_text("VM unsupported opcode fail-closed=PASS\r\n");
    }
    if (!vm_unknown_far_import_selftest()) {
        put_text("FAIL VM unknown far import was not rejected\r\n");
        failures = 1;
    } else {
        put_text("VM unknown far import fail-closed=PASS\r\n");
    }

    /* STATIC is a system window class; keep this top-level probe hidden. */
    g_probe_window = CreateWindow("STATIC", "W16API probe", 0L,
                                  0, 0, 1, 1,
                                  (HWND)0, (HMENU)0, instance,
                                  (void FAR *)0);
    if (g_probe_window == (HWND)0) {
        put_text("FAIL CreateWindow\r\n");
        failures = 1;
    } else {
        thunk = MakeProcInstance((FARPROC)EnumProc, instance);
        if (thunk == (FARPROC)0) {
            put_text("FAIL MakeProcInstance\r\n");
            failures = 1;
        } else {
            put_text("EnumWindows all-pass begin\r\n");
            enum_result = EnumWindows((WNDENUMPROC)thunk,
                                      (LPARAM)CALLBACK_COOKIE);
            put_text("EnumWindows all-pass result=");
            put_decimal((unsigned)enum_result);
            put_text(" callbacks=");
            put_decimal(g_all_count);
            put_text(" cookie_ok=");
            put_decimal((unsigned)g_cookie_ok);
            put_text(" probe_seen=");
            put_decimal((unsigned)g_probe_seen);
            put_newline();
            if (!enum_result || g_all_count == 0 || !g_cookie_ok ||
                !g_probe_seen || g_vm_failures != 0 ||
                g_vm_callback_invocations != g_all_count)
                failures = 1;

            g_stop_mode = 1;
            g_stop_count = 0;
            put_text("EnumWindows stop-on-first begin\r\n");
            enum_result = EnumWindows((WNDENUMPROC)thunk,
                                      (LPARAM)CALLBACK_COOKIE);
            put_text("EnumWindows stop result=");
            put_decimal((unsigned)enum_result);
            put_text(" callbacks=");
            put_decimal(g_stop_count);
            put_newline();
            if (enum_result || g_stop_count != 1 || g_vm_failures != 0 ||
                g_vm_callback_invocations != g_all_count + g_stop_count)
                failures = 1;

            FreeProcInstance(thunk);
        }
        DestroyWindow(g_probe_window);
    }

    put_text("VM callbacks=");
    put_decimal(g_vm_callback_invocations);
    put_text(" failures=");
    put_decimal(g_vm_failures);
    put_text(" getversion_calls=");
    put_decimal(g_vm_getversion_calls);
    put_text(" far_getversion_calls=");
    put_decimal(g_vm_far_getversion_calls);
    put_newline();
    put_text(failures ? "RESULT=FAIL\r\n" : "RESULT=PASS\r\n");
    _lclose(g_log);
    g_log = (HFILE)-1;
    /* This one-shot startup probe should leave Windows and return to DOS. */
    ExitWindows(0L, 0);
    return failures ? 1 : 0;
}
