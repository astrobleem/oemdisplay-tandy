
cdlg-timerfix-audit/CODE1.BIN:     file format binary


Disassembly of section .data:

00000000 <.data>:
       0:	45                   	inc    %bp
       1:	55                   	push   %bp
       2:	8b ec                	mov    %sp,%bp
       4:	1e                   	push   %ds
       5:	57                   	push   %di
       6:	1e                   	push   %ds
       7:	51                   	push   %cx
       8:	06                   	push   %es
       9:	56                   	push   %si
       a:	9a ff ff 00 00       	lcall  $0x0,$0xffff
       f:	1f                   	pop    %ds
      10:	5d                   	pop    %bp
      11:	4d                   	dec    %bp
      12:	cb                   	lret
      13:	45                   	inc    %bp
      14:	55                   	push   %bp
      15:	8b ec                	mov    %sp,%bp
      17:	1e                   	push   %ds
      18:	b4 19                	mov    $0x19,%ah
      1a:	cd 21                	int    $0x21
      1c:	32 e4                	xor    %ah,%ah
      1e:	1f                   	pop    %ds
      1f:	5d                   	pop    %bp
      20:	4d                   	dec    %bp
      21:	cb                   	lret
      22:	45                   	inc    %bp
      23:	55                   	push   %bp
      24:	8b ec                	mov    %sp,%bp
      26:	1e                   	push   %ds
      27:	52                   	push   %dx
      28:	8b 56 06             	mov    0x6(%bp),%dx
      2b:	b4 0e                	mov    $0xe,%ah
      2d:	cd 21                	int    $0x21
      2f:	5a                   	pop    %dx
      30:	1f                   	pop    %ds
      31:	5d                   	pop    %bp
      32:	4d                   	dec    %bp
      33:	ca 02 00             	lret   $0x2
      36:	45                   	inc    %bp
      37:	55                   	push   %bp
      38:	8b ec                	mov    %sp,%bp
      3a:	1e                   	push   %ds
      3b:	56                   	push   %si
      3c:	52                   	push   %dx
      3d:	8b 56 06             	mov    0x6(%bp),%dx
      40:	c5 76 08             	lds    0x8(%bp),%si
      43:	b4 47                	mov    $0x47,%ah
      45:	cd 21                	int    $0x21
      47:	b8 00 00             	mov    $0x0,%ax
      4a:	72 01                	jb     0x4d
      4c:	40                   	inc    %ax
      4d:	5a                   	pop    %dx
      4e:	5e                   	pop    %si
      4f:	1f                   	pop    %ds
      50:	5d                   	pop    %bp
      51:	4d                   	dec    %bp
      52:	ca 06 00             	lret   $0x6
      55:	45                   	inc    %bp
      56:	55                   	push   %bp
      57:	8b ec                	mov    %sp,%bp
      59:	1e                   	push   %ds
      5a:	52                   	push   %dx
      5b:	c5 56 06             	lds    0x6(%bp),%dx
      5e:	b4 3b                	mov    $0x3b,%ah
      60:	cd 21                	int    $0x21
      62:	b8 00 00             	mov    $0x0,%ax
      65:	72 01                	jb     0x68
      67:	40                   	inc    %ax
      68:	5a                   	pop    %dx
      69:	1f                   	pop    %ds
      6a:	5d                   	pop    %bp
      6b:	4d                   	dec    %bp
      6c:	ca 04 00             	lret   $0x4
      6f:	45                   	inc    %bp
      70:	55                   	push   %bp
      71:	8b ec                	mov    %sp,%bp
      73:	1e                   	push   %ds
      74:	52                   	push   %dx
      75:	51                   	push   %cx
      76:	c5 56 06             	lds    0x6(%bp),%dx
      79:	b8 00 43             	mov    $0x4300,%ax
      7c:	cd 21                	int    $0x21
      7e:	72 05                	jb     0x85
      80:	8b c1                	mov    %cx,%ax
      82:	eb 04                	jmp    0x88
      84:	90                   	nop
      85:	b8 ff ff             	mov    $0xffff,%ax
      88:	59                   	pop    %cx
      89:	5a                   	pop    %dx
      8a:	1f                   	pop    %ds
      8b:	5d                   	pop    %bp
      8c:	4d                   	dec    %bp
      8d:	ca 04 00             	lret   $0x4
      90:	45                   	inc    %bp
      91:	55                   	push   %bp
      92:	8b ec                	mov    %sp,%bp
      94:	1e                   	push   %ds
      95:	52                   	push   %dx
      96:	51                   	push   %cx
      97:	c5 56 06             	lds    0x6(%bp),%dx
      9a:	33 c9                	xor    %cx,%cx
      9c:	b8 00 5b             	mov    $0x5b00,%ax
      9f:	cd 21                	int    $0x21
      a1:	73 03                	jae    0xa6
      a3:	b8 ff ff             	mov    $0xffff,%ax
      a6:	59                   	pop    %cx
      a7:	5a                   	pop    %dx
      a8:	1f                   	pop    %ds
      a9:	5d                   	pop    %bp
      aa:	4d                   	dec    %bp
      ab:	ca 04 00             	lret   $0x4
      ae:	55                   	push   %bp
      af:	8b ec                	mov    %sp,%bp
      b1:	81 ec 06 00          	sub    $0x6,%sp
      b5:	57                   	push   %di
      b6:	56                   	push   %si
      b7:	9a ff ff 00 00       	lcall  $0x0,$0xffff
      bc:	89 46 fc             	mov    %ax,-0x4(%bp)
      bf:	c7 46 fe ff ff       	movw   $0xffff,-0x2(%bp)
      c4:	c7 46 fa 00 00       	movw   $0x0,-0x6(%bp)
      c9:	e9 03 00             	jmp    0xcf
      cc:	ff 46 fa             	incw   -0x6(%bp)
      cf:	83 7e fa 20          	cmpw   $0x20,-0x6(%bp)
      d3:	7c 03                	jl     0xd8
      d5:	e9 48 00             	jmp    0x120
      d8:	8b 46 fc             	mov    -0x4(%bp),%ax
      db:	8b 5e fa             	mov    -0x6(%bp),%bx
      de:	8b cb                	mov    %bx,%cx
      e0:	d1 e3                	shl    $1,%bx
      e2:	d1 e3                	shl    $1,%bx
      e4:	03 d9                	add    %cx,%bx
      e6:	d1 e3                	shl    $1,%bx
      e8:	39 87 20 02          	cmp    %ax,0x220(%bx)
      ec:	74 03                	je     0xf1
      ee:	e9 06 00             	jmp    0xf7
      f1:	8b 46 fa             	mov    -0x6(%bp),%ax
      f4:	e9 76 00             	jmp    0x16d
      f7:	8b 5e fa             	mov    -0x6(%bp),%bx
      fa:	8b c3                	mov    %bx,%ax
      fc:	d1 e3                	shl    $1,%bx
      fe:	d1 e3                	shl    $1,%bx
     100:	03 d8                	add    %ax,%bx
     102:	d1 e3                	shl    $1,%bx
     104:	83 bf 20 02 00       	cmpw   $0x0,0x220(%bx)
     109:	74 03                	je     0x10e
     10b:	e9 0f 00             	jmp    0x11d
     10e:	83 7e fe 00          	cmpw   $0x0,-0x2(%bp)
     112:	7c 03                	jl     0x117
     114:	e9 06 00             	jmp    0x11d
     117:	8b 46 fa             	mov    -0x6(%bp),%ax
     11a:	89 46 fe             	mov    %ax,-0x2(%bp)
     11d:	e9 ac ff             	jmp    0xcc
     120:	83 7e fe 00          	cmpw   $0x0,-0x2(%bp)
     124:	7d 03                	jge    0x129
     126:	e9 3e 00             	jmp    0x167
     129:	8b 46 fc             	mov    -0x4(%bp),%ax
     12c:	8b 5e fe             	mov    -0x2(%bp),%bx
     12f:	8b cb                	mov    %bx,%cx
     131:	d1 e3                	shl    $1,%bx
     133:	d1 e3                	shl    $1,%bx
     135:	03 d9                	add    %cx,%bx
     137:	d1 e3                	shl    $1,%bx
     139:	89 87 20 02          	mov    %ax,0x220(%bx)
     13d:	8b 5e fe             	mov    -0x2(%bp),%bx
     140:	8b c3                	mov    %bx,%ax
     142:	d1 e3                	shl    $1,%bx
     144:	d1 e3                	shl    $1,%bx
     146:	03 d8                	add    %ax,%bx
     148:	d1 e3                	shl    $1,%bx
     14a:	2b c0                	sub    %ax,%ax
     14c:	89 87 24 02          	mov    %ax,0x224(%bx)
     150:	89 87 22 02          	mov    %ax,0x222(%bx)
     154:	8b 5e fe             	mov    -0x2(%bp),%bx
     157:	8b c3                	mov    %bx,%ax
     159:	d1 e3                	shl    $1,%bx
     15b:	d1 e3                	shl    $1,%bx
     15d:	03 d8                	add    %ax,%bx
     15f:	d1 e3                	shl    $1,%bx
     161:	c7 87 26 02 00 00    	movw   $0x0,0x226(%bx)
     167:	8b 46 fe             	mov    -0x2(%bp),%ax
     16a:	e9 00 00             	jmp    0x16d
     16d:	5e                   	pop    %si
     16e:	5f                   	pop    %di
     16f:	8b e5                	mov    %bp,%sp
     171:	5d                   	pop    %bp
     172:	c3                   	ret
     173:	55                   	push   %bp
     174:	8b ec                	mov    %sp,%bp
     176:	81 ec 00 00          	sub    $0x0,%sp
     17a:	57                   	push   %di
     17b:	56                   	push   %si
     17c:	8b 46 06             	mov    0x6(%bp),%ax
     17f:	0b 46 04             	or     0x4(%bp),%ax
     182:	75 03                	jne    0x187
     184:	e9 26 00             	jmp    0x1ad
     187:	8b 46 04             	mov    0x4(%bp),%ax
     18a:	2b d2                	sub    %dx,%dx
     18c:	03 46 08             	add    0x8(%bp),%ax
     18f:	83 d2 00             	adc    $0x0,%dx
     192:	83 fa 01             	cmp    $0x1,%dx
     195:	76 03                	jbe    0x19a
     197:	e9 13 00             	jmp    0x1ad
     19a:	73 03                	jae    0x19f
     19c:	e9 08 00             	jmp    0x1a7
     19f:	3d 00 00             	cmp    $0x0,%ax
     1a2:	76 03                	jbe    0x1a7
     1a4:	e9 06 00             	jmp    0x1ad
     1a7:	b8 01 00             	mov    $0x1,%ax
     1aa:	e9 03 00             	jmp    0x1b0
     1ad:	b8 00 00             	mov    $0x0,%ax
     1b0:	e9 00 00             	jmp    0x1b3
     1b3:	5e                   	pop    %si
     1b4:	5f                   	pop    %di
     1b5:	8b e5                	mov    %bp,%sp
     1b7:	5d                   	pop    %bp
     1b8:	c3                   	ret
     1b9:	55                   	push   %bp
     1ba:	8b ec                	mov    %sp,%bp
     1bc:	81 ec 02 00          	sub    $0x2,%sp
     1c0:	57                   	push   %di
     1c1:	56                   	push   %si
     1c2:	8b 46 06             	mov    0x6(%bp),%ax
     1c5:	0b 46 04             	or     0x4(%bp),%ax
     1c8:	74 03                	je     0x1cd
     1ca:	e9 06 00             	jmp    0x1d3
     1cd:	8b 46 08             	mov    0x8(%bp),%ax
     1d0:	e9 53 00             	jmp    0x226
     1d3:	c7 46 fe 00 00       	movw   $0x0,-0x2(%bp)
     1d8:	e9 03 00             	jmp    0x1de
     1db:	ff 46 fe             	incw   -0x2(%bp)
     1de:	8b 46 08             	mov    0x8(%bp),%ax
     1e1:	39 46 fe             	cmp    %ax,-0x2(%bp)
     1e4:	72 03                	jb     0x1e9
     1e6:	e9 37 00             	jmp    0x220
     1e9:	8b 46 fe             	mov    -0x2(%bp),%ax
     1ec:	40                   	inc    %ax
     1ed:	50                   	push   %ax
     1ee:	ff 76 06             	push   0x6(%bp)
     1f1:	ff 76 04             	push   0x4(%bp)
     1f4:	e8 7c ff             	call   0x173
     1f7:	83 c4 06             	add    $0x6,%sp
     1fa:	3d 00 00             	cmp    $0x0,%ax
     1fd:	74 03                	je     0x202
     1ff:	e9 06 00             	jmp    0x208
     202:	8b 46 08             	mov    0x8(%bp),%ax
     205:	e9 1e 00             	jmp    0x226
     208:	c4 5e 04             	les    0x4(%bp),%bx
     20b:	8b 76 fe             	mov    -0x2(%bp),%si
     20e:	26 80 38 00          	cmpb   $0x0,%es:(%bx,%si)
     212:	74 03                	je     0x217
     214:	e9 06 00             	jmp    0x21d
     217:	8b 46 fe             	mov    -0x2(%bp),%ax
     21a:	e9 09 00             	jmp    0x226
     21d:	e9 bb ff             	jmp    0x1db
     220:	8b 46 08             	mov    0x8(%bp),%ax
     223:	e9 00 00             	jmp    0x226
     226:	5e                   	pop    %si
     227:	5f                   	pop    %di
     228:	8b e5                	mov    %bp,%sp
     22a:	5d                   	pop    %bp
     22b:	c3                   	ret
     22c:	55                   	push   %bp
     22d:	8b ec                	mov    %sp,%bp
     22f:	81 ec 04 00          	sub    $0x4,%sp
     233:	57                   	push   %di
     234:	56                   	push   %si
     235:	ff 76 0c             	push   0xc(%bp)
     238:	ff 76 0a             	push   0xa(%bp)
     23b:	ff 76 08             	push   0x8(%bp)
     23e:	e8 78 ff             	call   0x1b9
     241:	83 c4 06             	add    $0x6,%sp
     244:	89 46 fc             	mov    %ax,-0x4(%bp)
     247:	3b 46 0c             	cmp    0xc(%bp),%ax
     24a:	74 03                	je     0x24f
     24c:	e9 06 00             	jmp    0x255
     24f:	b8 00 00             	mov    $0x0,%ax
     252:	e9 31 00             	jmp    0x286
     255:	c7 46 fe 00 00       	movw   $0x0,-0x2(%bp)
     25a:	e9 03 00             	jmp    0x260
     25d:	ff 46 fe             	incw   -0x2(%bp)
     260:	8b 46 fc             	mov    -0x4(%bp),%ax
     263:	39 46 fe             	cmp    %ax,-0x2(%bp)
     266:	76 03                	jbe    0x26b
     268:	e9 15 00             	jmp    0x280
     26b:	c4 5e 08             	les    0x8(%bp),%bx
     26e:	8b 76 fe             	mov    -0x2(%bp),%si
     271:	26 8a 00             	mov    %es:(%bx,%si),%al
     274:	c4 5e 04             	les    0x4(%bp),%bx
     277:	8b 76 fe             	mov    -0x2(%bp),%si
     27a:	26 88 00             	mov    %al,%es:(%bx,%si)
     27d:	e9 dd ff             	jmp    0x25d
     280:	b8 01 00             	mov    $0x1,%ax
     283:	e9 00 00             	jmp    0x286
     286:	5e                   	pop    %si
     287:	5f                   	pop    %di
     288:	8b e5                	mov    %bp,%sp
     28a:	5d                   	pop    %bp
     28b:	c3                   	ret
     28c:	55                   	push   %bp
     28d:	8b ec                	mov    %sp,%bp
     28f:	81 ec 00 00          	sub    $0x0,%sp
     293:	57                   	push   %di
     294:	56                   	push   %si
     295:	80 7e 04 61          	cmpb   $0x61,0x4(%bp)
     299:	7d 03                	jge    0x29e
     29b:	e9 11 00             	jmp    0x2af
     29e:	80 7e 04 7a          	cmpb   $0x7a,0x4(%bp)
     2a2:	7e 03                	jle    0x2a7
     2a4:	e9 08 00             	jmp    0x2af
     2a7:	8a 46 04             	mov    0x4(%bp),%al
     2aa:	2c 20                	sub    $0x20,%al
     2ac:	e9 03 00             	jmp    0x2b2
     2af:	8a 46 04             	mov    0x4(%bp),%al
     2b2:	e9 00 00             	jmp    0x2b5
     2b5:	5e                   	pop    %si
     2b6:	5f                   	pop    %di
     2b7:	8b e5                	mov    %bp,%sp
     2b9:	5d                   	pop    %bp
     2ba:	c3                   	ret
     2bb:	55                   	push   %bp
     2bc:	8b ec                	mov    %sp,%bp
     2be:	81 ec 00 00          	sub    $0x0,%sp
     2c2:	57                   	push   %di
     2c3:	56                   	push   %si
     2c4:	80 7e 04 21          	cmpb   $0x21,0x4(%bp)
     2c8:	73 03                	jae    0x2cd
     2ca:	e9 63 00             	jmp    0x330
     2cd:	80 7e 04 7f          	cmpb   $0x7f,0x4(%bp)
     2d1:	72 03                	jb     0x2d6
     2d3:	e9 5a 00             	jmp    0x330
     2d6:	80 7e 04 22          	cmpb   $0x22,0x4(%bp)
     2da:	75 03                	jne    0x2df
     2dc:	e9 51 00             	jmp    0x330
     2df:	80 7e 04 3c          	cmpb   $0x3c,0x4(%bp)
     2e3:	75 03                	jne    0x2e8
     2e5:	e9 48 00             	jmp    0x330
     2e8:	80 7e 04 3e          	cmpb   $0x3e,0x4(%bp)
     2ec:	75 03                	jne    0x2f1
     2ee:	e9 3f 00             	jmp    0x330
     2f1:	80 7e 04 7c          	cmpb   $0x7c,0x4(%bp)
     2f5:	75 03                	jne    0x2fa
     2f7:	e9 36 00             	jmp    0x330
     2fa:	80 7e 04 5b          	cmpb   $0x5b,0x4(%bp)
     2fe:	75 03                	jne    0x303
     300:	e9 2d 00             	jmp    0x330
     303:	80 7e 04 5d          	cmpb   $0x5d,0x4(%bp)
     307:	75 03                	jne    0x30c
     309:	e9 24 00             	jmp    0x330
     30c:	80 7e 04 2b          	cmpb   $0x2b,0x4(%bp)
     310:	75 03                	jne    0x315
     312:	e9 1b 00             	jmp    0x330
     315:	80 7e 04 3d          	cmpb   $0x3d,0x4(%bp)
     319:	75 03                	jne    0x31e
     31b:	e9 12 00             	jmp    0x330
     31e:	80 7e 04 2c          	cmpb   $0x2c,0x4(%bp)
     322:	75 03                	jne    0x327
     324:	e9 09 00             	jmp    0x330
     327:	80 7e 04 3b          	cmpb   $0x3b,0x4(%bp)
     32b:	74 03                	je     0x330
     32d:	e9 06 00             	jmp    0x336
     330:	b8 01 00             	mov    $0x1,%ax
     333:	e9 03 00             	jmp    0x339
     336:	b8 00 00             	mov    $0x0,%ax
     339:	e9 00 00             	jmp    0x33c
     33c:	5e                   	pop    %si
     33d:	5f                   	pop    %di
     33e:	8b e5                	mov    %bp,%sp
     340:	5d                   	pop    %bp
     341:	c3                   	ret
     342:	55                   	push   %bp
     343:	8b ec                	mov    %sp,%bp
     345:	81 ec 06 00          	sub    $0x6,%sp
     349:	57                   	push   %di
     34a:	56                   	push   %si
     34b:	c4 5e 04             	les    0x4(%bp),%bx
     34e:	26 8a 07             	mov    %es:(%bx),%al
     351:	50                   	push   %ax
     352:	e8 37 ff             	call   0x28c
     355:	83 c4 02             	add    $0x2,%sp
     358:	88 46 fe             	mov    %al,-0x2(%bp)
     35b:	83 7e 08 01          	cmpw   $0x1,0x8(%bp)
     35f:	77 03                	ja     0x364
     361:	e9 11 00             	jmp    0x375
     364:	c4 5e 04             	les    0x4(%bp),%bx
     367:	26 8a 47 01          	mov    %es:0x1(%bx),%al
     36b:	50                   	push   %ax
     36c:	e8 1d ff             	call   0x28c
     36f:	83 c4 02             	add    $0x2,%sp
     372:	e9 02 00             	jmp    0x377
     375:	b0 00                	mov    $0x0,%al
     377:	88 46 fc             	mov    %al,-0x4(%bp)
     37a:	83 7e 08 02          	cmpw   $0x2,0x8(%bp)
     37e:	77 03                	ja     0x383
     380:	e9 11 00             	jmp    0x394
     383:	c4 5e 04             	les    0x4(%bp),%bx
     386:	26 8a 47 02          	mov    %es:0x2(%bx),%al
     38a:	50                   	push   %ax
     38b:	e8 fe fe             	call   0x28c
     38e:	83 c4 02             	add    $0x2,%sp
     391:	e9 02 00             	jmp    0x396
     394:	b0 00                	mov    $0x0,%al
     396:	88 46 fa             	mov    %al,-0x6(%bp)
     399:	83 7e 08 03          	cmpw   $0x3,0x8(%bp)
     39d:	74 03                	je     0x3a2
     39f:	e9 72 00             	jmp    0x414
     3a2:	80 7e fe 43          	cmpb   $0x43,-0x2(%bp)
     3a6:	74 03                	je     0x3ab
     3a8:	e9 12 00             	jmp    0x3bd
     3ab:	80 7e fc 4f          	cmpb   $0x4f,-0x4(%bp)
     3af:	74 03                	je     0x3b4
     3b1:	e9 09 00             	jmp    0x3bd
     3b4:	80 7e fa 4e          	cmpb   $0x4e,-0x6(%bp)
     3b8:	75 03                	jne    0x3bd
     3ba:	e9 51 00             	jmp    0x40e
     3bd:	80 7e fe 41          	cmpb   $0x41,-0x2(%bp)
     3c1:	74 03                	je     0x3c6
     3c3:	e9 12 00             	jmp    0x3d8
     3c6:	80 7e fc 55          	cmpb   $0x55,-0x4(%bp)
     3ca:	74 03                	je     0x3cf
     3cc:	e9 09 00             	jmp    0x3d8
     3cf:	80 7e fa 58          	cmpb   $0x58,-0x6(%bp)
     3d3:	75 03                	jne    0x3d8
     3d5:	e9 36 00             	jmp    0x40e
     3d8:	80 7e fe 4e          	cmpb   $0x4e,-0x2(%bp)
     3dc:	74 03                	je     0x3e1
     3de:	e9 12 00             	jmp    0x3f3
     3e1:	80 7e fc 55          	cmpb   $0x55,-0x4(%bp)
     3e5:	74 03                	je     0x3ea
     3e7:	e9 09 00             	jmp    0x3f3
     3ea:	80 7e fa 4c          	cmpb   $0x4c,-0x6(%bp)
     3ee:	75 03                	jne    0x3f3
     3f0:	e9 1b 00             	jmp    0x40e
     3f3:	80 7e fe 50          	cmpb   $0x50,-0x2(%bp)
     3f7:	74 03                	je     0x3fc
     3f9:	e9 18 00             	jmp    0x414
     3fc:	80 7e fc 52          	cmpb   $0x52,-0x4(%bp)
     400:	74 03                	je     0x405
     402:	e9 0f 00             	jmp    0x414
     405:	80 7e fa 4e          	cmpb   $0x4e,-0x6(%bp)
     409:	74 03                	je     0x40e
     40b:	e9 06 00             	jmp    0x414
     40e:	b8 01 00             	mov    $0x1,%ax
     411:	e9 c6 00             	jmp    0x4da
     414:	83 7e 08 04          	cmpw   $0x4,0x8(%bp)
     418:	74 03                	je     0x41d
     41a:	e9 56 00             	jmp    0x473
     41d:	c4 5e 04             	les    0x4(%bp),%bx
     420:	26 80 7f 03 31       	cmpb   $0x31,%es:0x3(%bx)
     425:	7d 03                	jge    0x42a
     427:	e9 49 00             	jmp    0x473
     42a:	c4 5e 04             	les    0x4(%bp),%bx
     42d:	26 80 7f 03 39       	cmpb   $0x39,%es:0x3(%bx)
     432:	7e 03                	jle    0x437
     434:	e9 3c 00             	jmp    0x473
     437:	80 7e fe 43          	cmpb   $0x43,-0x2(%bp)
     43b:	74 03                	je     0x440
     43d:	e9 12 00             	jmp    0x452
     440:	80 7e fc 4f          	cmpb   $0x4f,-0x4(%bp)
     444:	74 03                	je     0x449
     446:	e9 09 00             	jmp    0x452
     449:	80 7e fa 4d          	cmpb   $0x4d,-0x6(%bp)
     44d:	75 03                	jne    0x452
     44f:	e9 1b 00             	jmp    0x46d
     452:	80 7e fe 4c          	cmpb   $0x4c,-0x2(%bp)
     456:	74 03                	je     0x45b
     458:	e9 18 00             	jmp    0x473
     45b:	80 7e fc 50          	cmpb   $0x50,-0x4(%bp)
     45f:	74 03                	je     0x464
     461:	e9 0f 00             	jmp    0x473
     464:	80 7e fa 54          	cmpb   $0x54,-0x6(%bp)
     468:	74 03                	je     0x46d
     46a:	e9 06 00             	jmp    0x473
     46d:	b8 01 00             	mov    $0x1,%ax
     470:	e9 67 00             	jmp    0x4da
     473:	83 7e 08 06          	cmpw   $0x6,0x8(%bp)
     477:	74 03                	je     0x47c
     479:	e9 58 00             	jmp    0x4d4
     47c:	80 7e fe 43          	cmpb   $0x43,-0x2(%bp)
     480:	74 03                	je     0x485
     482:	e9 4f 00             	jmp    0x4d4
     485:	80 7e fc 4c          	cmpb   $0x4c,-0x4(%bp)
     489:	74 03                	je     0x48e
     48b:	e9 46 00             	jmp    0x4d4
     48e:	80 7e fa 4f          	cmpb   $0x4f,-0x6(%bp)
     492:	74 03                	je     0x497
     494:	e9 3d 00             	jmp    0x4d4
     497:	c4 5e 04             	les    0x4(%bp),%bx
     49a:	26 8a 47 03          	mov    %es:0x3(%bx),%al
     49e:	50                   	push   %ax
     49f:	e8 ea fd             	call   0x28c
     4a2:	83 c4 02             	add    $0x2,%sp
     4a5:	3c 43                	cmp    $0x43,%al
     4a7:	74 03                	je     0x4ac
     4a9:	e9 28 00             	jmp    0x4d4
     4ac:	c4 5e 04             	les    0x4(%bp),%bx
     4af:	26 8a 47 04          	mov    %es:0x4(%bx),%al
     4b3:	50                   	push   %ax
     4b4:	e8 d5 fd             	call   0x28c
     4b7:	83 c4 02             	add    $0x2,%sp
     4ba:	3c 4b                	cmp    $0x4b,%al
     4bc:	74 03                	je     0x4c1
     4be:	e9 13 00             	jmp    0x4d4
     4c1:	c4 5e 04             	les    0x4(%bp),%bx
     4c4:	26 80 7f 05 24       	cmpb   $0x24,%es:0x5(%bx)
     4c9:	74 03                	je     0x4ce
     4cb:	e9 06 00             	jmp    0x4d4
     4ce:	b8 01 00             	mov    $0x1,%ax
     4d1:	e9 03 00             	jmp    0x4d7
     4d4:	b8 00 00             	mov    $0x0,%ax
     4d7:	e9 00 00             	jmp    0x4da
     4da:	5e                   	pop    %si
     4db:	5f                   	pop    %di
     4dc:	8b e5                	mov    %bp,%sp
     4de:	5d                   	pop    %bp
     4df:	c3                   	ret
     4e0:	55                   	push   %bp
     4e1:	8b ec                	mov    %sp,%bp
     4e3:	81 ec 10 00          	sub    $0x10,%sp
     4e7:	57                   	push   %di
     4e8:	56                   	push   %si
     4e9:	b8 80 00             	mov    $0x80,%ax
     4ec:	50                   	push   %ax
     4ed:	ff 76 06             	push   0x6(%bp)
     4f0:	ff 76 04             	push   0x4(%bp)
     4f3:	e8 c3 fc             	call   0x1b9
     4f6:	83 c4 06             	add    $0x6,%sp
     4f9:	89 46 f0             	mov    %ax,-0x10(%bp)
     4fc:	c7 46 f2 00 00       	movw   $0x0,-0xe(%bp)
     501:	83 7e f0 00          	cmpw   $0x0,-0x10(%bp)
     505:	75 03                	jne    0x50a
     507:	e9 0a 00             	jmp    0x514
     50a:	81 7e f0 80 00       	cmpw   $0x80,-0x10(%bp)
     50f:	74 03                	je     0x514
     511:	e9 06 00             	jmp    0x51a
     514:	b8 00 00             	mov    $0x0,%ax
     517:	e9 3d 02             	jmp    0x757
     51a:	c4 5e 04             	les    0x4(%bp),%bx
     51d:	26 80 3f 5c          	cmpb   $0x5c,%es:(%bx)
     521:	75 03                	jne    0x526
     523:	e9 0c 00             	jmp    0x532
     526:	c4 5e 04             	les    0x4(%bp),%bx
     529:	26 80 3f 2f          	cmpb   $0x2f,%es:(%bx)
     52d:	74 03                	je     0x532
     52f:	e9 20 00             	jmp    0x552
     532:	c4 5e 04             	les    0x4(%bp),%bx
     535:	26 80 7f 01 5c       	cmpb   $0x5c,%es:0x1(%bx)
     53a:	75 03                	jne    0x53f
     53c:	e9 0d 00             	jmp    0x54c
     53f:	c4 5e 04             	les    0x4(%bp),%bx
     542:	26 80 7f 01 2f       	cmpb   $0x2f,%es:0x1(%bx)
     547:	74 03                	je     0x54c
     549:	e9 06 00             	jmp    0x552
     54c:	b8 00 00             	mov    $0x0,%ax
     54f:	e9 05 02             	jmp    0x757
     552:	83 7e f0 01          	cmpw   $0x1,-0x10(%bp)
     556:	77 03                	ja     0x55b
     558:	e9 38 00             	jmp    0x593
     55b:	c4 5e 04             	les    0x4(%bp),%bx
     55e:	26 80 7f 01 3a       	cmpb   $0x3a,%es:0x1(%bx)
     563:	74 03                	je     0x568
     565:	e9 2b 00             	jmp    0x593
     568:	c4 5e 04             	les    0x4(%bp),%bx
     56b:	26 8a 07             	mov    %es:(%bx),%al
     56e:	50                   	push   %ax
     56f:	e8 1a fd             	call   0x28c
     572:	83 c4 02             	add    $0x2,%sp
     575:	88 46 fc             	mov    %al,-0x4(%bp)
     578:	3c 41                	cmp    $0x41,%al
     57a:	7d 03                	jge    0x57f
     57c:	e9 09 00             	jmp    0x588
     57f:	80 7e fc 5a          	cmpb   $0x5a,-0x4(%bp)
     583:	7f 03                	jg     0x588
     585:	e9 06 00             	jmp    0x58e
     588:	b8 00 00             	mov    $0x0,%ax
     58b:	e9 c9 01             	jmp    0x757
     58e:	c7 46 f2 02 00       	movw   $0x2,-0xe(%bp)
     593:	8b 46 f0             	mov    -0x10(%bp),%ax
     596:	39 46 f2             	cmp    %ax,-0xe(%bp)
     599:	74 03                	je     0x59e
     59b:	e9 06 00             	jmp    0x5a4
     59e:	b8 00 00             	mov    $0x0,%ax
     5a1:	e9 b3 01             	jmp    0x757
     5a4:	8b 46 f2             	mov    -0xe(%bp),%ax
     5a7:	89 46 f8             	mov    %ax,-0x8(%bp)
     5aa:	e9 03 00             	jmp    0x5b0
     5ad:	ff 46 f8             	incw   -0x8(%bp)
     5b0:	8b 46 f0             	mov    -0x10(%bp),%ax
     5b3:	39 46 f8             	cmp    %ax,-0x8(%bp)
     5b6:	76 03                	jbe    0x5bb
     5b8:	e9 96 01             	jmp    0x751
     5bb:	c4 5e 04             	les    0x4(%bp),%bx
     5be:	8b 76 f8             	mov    -0x8(%bp),%si
     5c1:	26 80 38 5c          	cmpb   $0x5c,%es:(%bx,%si)
     5c5:	75 03                	jne    0x5ca
     5c7:	e9 1e 00             	jmp    0x5e8
     5ca:	c4 5e 04             	les    0x4(%bp),%bx
     5cd:	8b 76 f8             	mov    -0x8(%bp),%si
     5d0:	26 80 38 2f          	cmpb   $0x2f,%es:(%bx,%si)
     5d4:	75 03                	jne    0x5d9
     5d6:	e9 0f 00             	jmp    0x5e8
     5d9:	c4 5e 04             	les    0x4(%bp),%bx
     5dc:	8b 76 f8             	mov    -0x8(%bp),%si
     5df:	26 80 38 00          	cmpb   $0x0,%es:(%bx,%si)
     5e3:	74 03                	je     0x5e8
     5e5:	e9 66 01             	jmp    0x74e
     5e8:	8b 46 f8             	mov    -0x8(%bp),%ax
     5eb:	39 46 f2             	cmp    %ax,-0xe(%bp)
     5ee:	74 03                	je     0x5f3
     5f0:	e9 1b 00             	jmp    0x60e
     5f3:	8b 46 f0             	mov    -0x10(%bp),%ax
     5f6:	39 46 f8             	cmp    %ax,-0x8(%bp)
     5f9:	74 03                	je     0x5fe
     5fb:	e9 06 00             	jmp    0x604
     5fe:	b8 00 00             	mov    $0x0,%ax
     601:	e9 53 01             	jmp    0x757
     604:	8b 46 f8             	mov    -0x8(%bp),%ax
     607:	40                   	inc    %ax
     608:	89 46 f2             	mov    %ax,-0xe(%bp)
     60b:	e9 9f ff             	jmp    0x5ad
     60e:	8b 46 f8             	mov    -0x8(%bp),%ax
     611:	2b 46 f2             	sub    -0xe(%bp),%ax
     614:	48                   	dec    %ax
     615:	74 03                	je     0x61a
     617:	e9 0f 00             	jmp    0x629
     61a:	c4 5e 04             	les    0x4(%bp),%bx
     61d:	8b 76 f2             	mov    -0xe(%bp),%si
     620:	26 80 38 2e          	cmpb   $0x2e,%es:(%bx,%si)
     624:	75 03                	jne    0x629
     626:	e9 2d 00             	jmp    0x656
     629:	8b 46 f8             	mov    -0x8(%bp),%ax
     62c:	2b 46 f2             	sub    -0xe(%bp),%ax
     62f:	3d 02 00             	cmp    $0x2,%ax
     632:	74 03                	je     0x637
     634:	e9 33 00             	jmp    0x66a
     637:	c4 5e 04             	les    0x4(%bp),%bx
     63a:	8b 76 f2             	mov    -0xe(%bp),%si
     63d:	26 80 38 2e          	cmpb   $0x2e,%es:(%bx,%si)
     641:	74 03                	je     0x646
     643:	e9 24 00             	jmp    0x66a
     646:	c4 5e 04             	les    0x4(%bp),%bx
     649:	8b 76 f2             	mov    -0xe(%bp),%si
     64c:	26 80 78 01 2e       	cmpb   $0x2e,%es:0x1(%bx,%si)
     651:	74 03                	je     0x656
     653:	e9 14 00             	jmp    0x66a
     656:	8b 46 f0             	mov    -0x10(%bp),%ax
     659:	39 46 f8             	cmp    %ax,-0x8(%bp)
     65c:	74 03                	je     0x661
     65e:	e9 06 00             	jmp    0x667
     661:	b8 00 00             	mov    $0x0,%ax
     664:	e9 f0 00             	jmp    0x757
     667:	e9 dd 00             	jmp    0x747
     66a:	b8 00 00             	mov    $0x0,%ax
     66d:	89 46 fe             	mov    %ax,-0x2(%bp)
     670:	89 46 f4             	mov    %ax,-0xc(%bp)
     673:	c7 46 fa 00 00       	movw   $0x0,-0x6(%bp)
     678:	8b 46 f2             	mov    -0xe(%bp),%ax
     67b:	89 46 f6             	mov    %ax,-0xa(%bp)
     67e:	e9 03 00             	jmp    0x684
     681:	ff 46 f6             	incw   -0xa(%bp)
     684:	8b 46 f8             	mov    -0x8(%bp),%ax
     687:	39 46 f6             	cmp    %ax,-0xa(%bp)
     68a:	72 03                	jb     0x68f
     68c:	e9 7b 00             	jmp    0x70a
     68f:	c4 5e 04             	les    0x4(%bp),%bx
     692:	8b 76 f6             	mov    -0xa(%bp),%si
     695:	26 8a 00             	mov    %es:(%bx,%si),%al
     698:	88 46 fc             	mov    %al,-0x4(%bp)
     69b:	3c 2e                	cmp    $0x2e,%al
     69d:	74 03                	je     0x6a2
     69f:	e9 17 00             	jmp    0x6b9
     6a2:	83 7e fa 00          	cmpw   $0x0,-0x6(%bp)
     6a6:	75 03                	jne    0x6ab
     6a8:	e9 06 00             	jmp    0x6b1
     6ab:	b8 00 00             	mov    $0x0,%ax
     6ae:	e9 a6 00             	jmp    0x757
     6b1:	c7 46 fa 01 00       	movw   $0x1,-0x6(%bp)
     6b6:	e9 4e 00             	jmp    0x707
     6b9:	8a 46 fc             	mov    -0x4(%bp),%al
     6bc:	50                   	push   %ax
     6bd:	e8 fb fb             	call   0x2bb
     6c0:	83 c4 02             	add    $0x2,%sp
     6c3:	3d 00 00             	cmp    $0x0,%ax
     6c6:	74 03                	je     0x6cb
     6c8:	e9 24 00             	jmp    0x6ef
     6cb:	80 7e fc 3a          	cmpb   $0x3a,-0x4(%bp)
     6cf:	75 03                	jne    0x6d4
     6d1:	e9 1b 00             	jmp    0x6ef
     6d4:	80 7e fc 2a          	cmpb   $0x2a,-0x4(%bp)
     6d8:	75 03                	jne    0x6dd
     6da:	e9 09 00             	jmp    0x6e6
     6dd:	80 7e fc 3f          	cmpb   $0x3f,-0x4(%bp)
     6e1:	74 03                	je     0x6e6
     6e3:	e9 0f 00             	jmp    0x6f5
     6e6:	83 7e 08 00          	cmpw   $0x0,0x8(%bp)
     6ea:	74 03                	je     0x6ef
     6ec:	e9 06 00             	jmp    0x6f5
     6ef:	b8 00 00             	mov    $0x0,%ax
     6f2:	e9 62 00             	jmp    0x757
     6f5:	83 7e fa 00          	cmpw   $0x0,-0x6(%bp)
     6f9:	75 03                	jne    0x6fe
     6fb:	e9 06 00             	jmp    0x704
     6fe:	ff 46 fe             	incw   -0x2(%bp)
     701:	e9 03 00             	jmp    0x707
     704:	ff 46 f4             	incw   -0xc(%bp)
     707:	e9 77 ff             	jmp    0x681
     70a:	83 7e f4 00          	cmpw   $0x0,-0xc(%bp)
     70e:	75 03                	jne    0x713
     710:	e9 2e 00             	jmp    0x741
     713:	83 7e f4 08          	cmpw   $0x8,-0xc(%bp)
     717:	76 03                	jbe    0x71c
     719:	e9 25 00             	jmp    0x741
     71c:	83 7e fe 03          	cmpw   $0x3,-0x2(%bp)
     720:	76 03                	jbe    0x725
     722:	e9 1c 00             	jmp    0x741
     725:	ff 76 f4             	push   -0xc(%bp)
     728:	8b 46 04             	mov    0x4(%bp),%ax
     72b:	8b 56 06             	mov    0x6(%bp),%dx
     72e:	03 46 f2             	add    -0xe(%bp),%ax
     731:	52                   	push   %dx
     732:	50                   	push   %ax
     733:	e8 0c fc             	call   0x342
     736:	83 c4 06             	add    $0x6,%sp
     739:	3d 00 00             	cmp    $0x0,%ax
     73c:	75 03                	jne    0x741
     73e:	e9 06 00             	jmp    0x747
     741:	b8 00 00             	mov    $0x0,%ax
     744:	e9 10 00             	jmp    0x757
     747:	8b 46 f8             	mov    -0x8(%bp),%ax
     74a:	40                   	inc    %ax
     74b:	89 46 f2             	mov    %ax,-0xe(%bp)
     74e:	e9 5c fe             	jmp    0x5ad
     751:	b8 01 00             	mov    $0x1,%ax
     754:	e9 00 00             	jmp    0x757
     757:	5e                   	pop    %si
     758:	5f                   	pop    %di
     759:	8b e5                	mov    %bp,%sp
     75b:	5d                   	pop    %bp
     75c:	c3                   	ret
     75d:	55                   	push   %bp
     75e:	8b ec                	mov    %sp,%bp
     760:	81 ec 08 00          	sub    $0x8,%sp
     764:	57                   	push   %di
     765:	56                   	push   %si
     766:	b8 80 00             	mov    $0x80,%ax
     769:	50                   	push   %ax
     76a:	ff 76 06             	push   0x6(%bp)
     76d:	ff 76 04             	push   0x4(%bp)
     770:	e8 46 fa             	call   0x1b9
     773:	83 c4 06             	add    $0x6,%sp
     776:	89 46 f8             	mov    %ax,-0x8(%bp)
     779:	c7 46 fa 00 00       	movw   $0x0,-0x6(%bp)
     77e:	b8 00 00             	mov    $0x0,%ax
     781:	50                   	push   %ax
     782:	ff 76 06             	push   0x6(%bp)
     785:	ff 76 04             	push   0x4(%bp)
     788:	e8 55 fd             	call   0x4e0
     78b:	83 c4 06             	add    $0x6,%sp
     78e:	3d 00 00             	cmp    $0x0,%ax
     791:	74 03                	je     0x796
     793:	e9 06 00             	jmp    0x79c
     796:	b8 ff ff             	mov    $0xffff,%ax
     799:	e9 b6 00             	jmp    0x852
     79c:	c7 46 fe 00 00       	movw   $0x0,-0x2(%bp)
     7a1:	e9 03 00             	jmp    0x7a7
     7a4:	ff 46 fe             	incw   -0x2(%bp)
     7a7:	8b 46 f8             	mov    -0x8(%bp),%ax
     7aa:	39 46 fe             	cmp    %ax,-0x2(%bp)
     7ad:	72 03                	jb     0x7b2
     7af:	e9 37 00             	jmp    0x7e9
     7b2:	c4 5e 04             	les    0x4(%bp),%bx
     7b5:	8b 76 fe             	mov    -0x2(%bp),%si
     7b8:	26 80 38 5c          	cmpb   $0x5c,%es:(%bx,%si)
     7bc:	75 03                	jne    0x7c1
     7be:	e9 1e 00             	jmp    0x7df
     7c1:	c4 5e 04             	les    0x4(%bp),%bx
     7c4:	8b 76 fe             	mov    -0x2(%bp),%si
     7c7:	26 80 38 2f          	cmpb   $0x2f,%es:(%bx,%si)
     7cb:	75 03                	jne    0x7d0
     7cd:	e9 0f 00             	jmp    0x7df
     7d0:	c4 5e 04             	les    0x4(%bp),%bx
     7d3:	8b 76 fe             	mov    -0x2(%bp),%si
     7d6:	26 80 38 3a          	cmpb   $0x3a,%es:(%bx,%si)
     7da:	74 03                	je     0x7df
     7dc:	e9 07 00             	jmp    0x7e6
     7df:	8b 46 fe             	mov    -0x2(%bp),%ax
     7e2:	40                   	inc    %ax
     7e3:	89 46 fa             	mov    %ax,-0x6(%bp)
     7e6:	e9 bb ff             	jmp    0x7a4
     7e9:	8b 46 f8             	mov    -0x8(%bp),%ax
     7ec:	2b 46 fa             	sub    -0x6(%bp),%ax
     7ef:	40                   	inc    %ax
     7f0:	89 46 fc             	mov    %ax,-0x4(%bp)
     7f3:	3b 46 0c             	cmp    0xc(%bp),%ax
     7f6:	77 03                	ja     0x7fb
     7f8:	e9 06 00             	jmp    0x801
     7fb:	8b 46 fc             	mov    -0x4(%bp),%ax
     7fe:	e9 51 00             	jmp    0x852
     801:	ff 76 fc             	push   -0x4(%bp)
     804:	ff 76 0a             	push   0xa(%bp)
     807:	ff 76 08             	push   0x8(%bp)
     80a:	e8 66 f9             	call   0x173
     80d:	83 c4 06             	add    $0x6,%sp
     810:	3d 00 00             	cmp    $0x0,%ax
     813:	74 03                	je     0x818
     815:	e9 06 00             	jmp    0x81e
     818:	b8 ff ff             	mov    $0xffff,%ax
     81b:	e9 34 00             	jmp    0x852
     81e:	c7 46 fe 00 00       	movw   $0x0,-0x2(%bp)
     823:	e9 03 00             	jmp    0x829
     826:	ff 46 fe             	incw   -0x2(%bp)
     829:	8b 46 fe             	mov    -0x2(%bp),%ax
     82c:	39 46 fc             	cmp    %ax,-0x4(%bp)
     82f:	77 03                	ja     0x834
     831:	e9 18 00             	jmp    0x84c
     834:	c4 5e 04             	les    0x4(%bp),%bx
     837:	03 5e fa             	add    -0x6(%bp),%bx
     83a:	8b 76 fe             	mov    -0x2(%bp),%si
     83d:	26 8a 00             	mov    %es:(%bx,%si),%al
     840:	c4 5e 08             	les    0x8(%bp),%bx
     843:	8b 76 fe             	mov    -0x2(%bp),%si
     846:	26 88 00             	mov    %al,%es:(%bx,%si)
     849:	e9 da ff             	jmp    0x826
     84c:	b8 00 00             	mov    $0x0,%ax
     84f:	e9 00 00             	jmp    0x852
     852:	5e                   	pop    %si
     853:	5f                   	pop    %di
     854:	8b e5                	mov    %bp,%sp
     856:	5d                   	pop    %bp
     857:	c3                   	ret
     858:	1e                   	push   %ds
     859:	58                   	pop    %ax
     85a:	90                   	nop
     85b:	45                   	inc    %bp
     85c:	55                   	push   %bp
     85d:	8b ec                	mov    %sp,%bp
     85f:	1e                   	push   %ds
     860:	8e d8                	mov    %ax,%ds
     862:	81 ec 06 00          	sub    $0x6,%sp
     866:	57                   	push   %di
     867:	56                   	push   %si
     868:	e8 43 f8             	call   0xae
     86b:	89 46 fa             	mov    %ax,-0x6(%bp)
     86e:	3d 00 00             	cmp    $0x0,%ax
     871:	7d 03                	jge    0x876
     873:	e9 17 00             	jmp    0x88d
     876:	8b 5e fa             	mov    -0x6(%bp),%bx
     879:	8b c3                	mov    %bx,%ax
     87b:	d1 e3                	shl    $1,%bx
     87d:	d1 e3                	shl    $1,%bx
     87f:	03 d8                	add    %ax,%bx
     881:	d1 e3                	shl    $1,%bx
     883:	2b c0                	sub    %ax,%ax
     885:	89 87 24 02          	mov    %ax,0x224(%bx)
     889:	89 87 22 02          	mov    %ax,0x222(%bx)
     88d:	ff 76 06             	push   0x6(%bp)
     890:	ff 76 0a             	push   0xa(%bp)
     893:	ff 76 08             	push   0x8(%bp)
     896:	ff 76 0e             	push   0xe(%bp)
     899:	ff 76 0c             	push   0xc(%bp)
     89c:	e8 be fe             	call   0x75d
     89f:	83 c4 0a             	add    $0xa,%sp
     8a2:	89 46 fc             	mov    %ax,-0x4(%bp)
     8a5:	83 7e fa 00          	cmpw   $0x0,-0x6(%bp)
     8a9:	7d 03                	jge    0x8ae
     8ab:	e9 22 00             	jmp    0x8d0
     8ae:	83 7e fc 00          	cmpw   $0x0,-0x4(%bp)
     8b2:	7c 03                	jl     0x8b7
     8b4:	e9 19 00             	jmp    0x8d0
     8b7:	8b 5e fa             	mov    -0x6(%bp),%bx
     8ba:	8b c3                	mov    %bx,%ax
     8bc:	d1 e3                	shl    $1,%bx
     8be:	d1 e3                	shl    $1,%bx
     8c0:	03 d8                	add    %ax,%bx
     8c2:	d1 e3                	shl    $1,%bx
     8c4:	c7 87 22 02 02 30    	movw   $0x3002,0x222(%bx)
     8ca:	c7 87 24 02 00 00    	movw   $0x0,0x224(%bx)
     8d0:	8b 46 fc             	mov    -0x4(%bp),%ax
     8d3:	e9 00 00             	jmp    0x8d6
     8d6:	5e                   	pop    %si
     8d7:	5f                   	pop    %di
     8d8:	83 ed 02             	sub    $0x2,%bp
     8db:	8b e5                	mov    %bp,%sp
     8dd:	1f                   	pop    %ds
     8de:	5d                   	pop    %bp
     8df:	4d                   	dec    %bp
     8e0:	ca 0a 00             	lret   $0xa
     8e3:	1e                   	push   %ds
     8e4:	58                   	pop    %ax
     8e5:	90                   	nop
     8e6:	45                   	inc    %bp
     8e7:	55                   	push   %bp
     8e8:	8b ec                	mov    %sp,%bp
     8ea:	1e                   	push   %ds
     8eb:	8e d8                	mov    %ax,%ds
     8ed:	81 ec 04 00          	sub    $0x4,%sp
     8f1:	57                   	push   %di
     8f2:	56                   	push   %si
     8f3:	e8 b8 f7             	call   0xae
     8f6:	89 46 fc             	mov    %ax,-0x4(%bp)
     8f9:	3d 00 00             	cmp    $0x0,%ax
     8fc:	7d 03                	jge    0x901
     8fe:	e9 18 00             	jmp    0x919
     901:	8b 5e fc             	mov    -0x4(%bp),%bx
     904:	8b c3                	mov    %bx,%ax
     906:	d1 e3                	shl    $1,%bx
     908:	d1 e3                	shl    $1,%bx
     90a:	03 d8                	add    %ax,%bx
     90c:	d1 e3                	shl    $1,%bx
     90e:	8b 87 22 02          	mov    0x222(%bx),%ax
     912:	8b 97 24 02          	mov    0x224(%bx),%dx
     916:	e9 06 00             	jmp    0x91f
     919:	b8 09 00             	mov    $0x9,%ax
     91c:	ba 00 00             	mov    $0x0,%dx
     91f:	e9 00 00             	jmp    0x922
     922:	5e                   	pop    %si
     923:	5f                   	pop    %di
     924:	83 ed 02             	sub    $0x2,%bp
     927:	8b e5                	mov    %bp,%sp
     929:	1f                   	pop    %ds
     92a:	5d                   	pop    %bp
     92b:	4d                   	dec    %bp
     92c:	cb                   	lret
     92d:	1e                   	push   %ds
     92e:	58                   	pop    %ax
     92f:	90                   	nop
     930:	45                   	inc    %bp
     931:	55                   	push   %bp
     932:	8b ec                	mov    %sp,%bp
     934:	1e                   	push   %ds
     935:	8e d8                	mov    %ax,%ds
     937:	81 ec 00 00          	sub    $0x0,%sp
     93b:	57                   	push   %di
     93c:	56                   	push   %si
     93d:	8b 46 0e             	mov    0xe(%bp),%ax
     940:	a3 1e 02             	mov    %ax,0x21e
     943:	83 7e 0a 00          	cmpw   $0x0,0xa(%bp)
     947:	75 03                	jne    0x94c
     949:	e9 1d 00             	jmp    0x969
     94c:	ff 76 0c             	push   0xc(%bp)
     94f:	b8 00 00             	mov    $0x0,%ax
     952:	50                   	push   %ax
     953:	ff 76 0a             	push   0xa(%bp)
     956:	9a ff ff 00 00       	lcall  $0x0,$0xffff
     95b:	3d 00 00             	cmp    $0x0,%ax
     95e:	74 03                	je     0x963
     960:	e9 06 00             	jmp    0x969
     963:	b8 00 00             	mov    $0x0,%ax
     966:	e9 06 00             	jmp    0x96f
     969:	b8 01 00             	mov    $0x1,%ax
     96c:	e9 00 00             	jmp    0x96f
     96f:	5e                   	pop    %si
     970:	5f                   	pop    %di
     971:	83 ed 02             	sub    $0x2,%bp
     974:	8b e5                	mov    %bp,%sp
     976:	1f                   	pop    %ds
     977:	5d                   	pop    %bp
     978:	4d                   	dec    %bp
     979:	ca 0a 00             	lret   $0xa
     97c:	1e                   	push   %ds
     97d:	58                   	pop    %ax
     97e:	90                   	nop
     97f:	45                   	inc    %bp
     980:	55                   	push   %bp
     981:	8b ec                	mov    %sp,%bp
     983:	1e                   	push   %ds
     984:	8e d8                	mov    %ax,%ds
     986:	81 ec 00 00          	sub    $0x0,%sp
     98a:	57                   	push   %di
     98b:	56                   	push   %si
     98c:	b8 01 00             	mov    $0x1,%ax
     98f:	e9 00 00             	jmp    0x992
     992:	5e                   	pop    %si
     993:	5f                   	pop    %di
     994:	83 ed 02             	sub    $0x2,%bp
     997:	8b e5                	mov    %bp,%sp
     999:	1f                   	pop    %ds
     99a:	5d                   	pop    %bp
     99b:	4d                   	dec    %bp
     99c:	ca 02 00             	lret   $0x2
     99f:	55                   	push   %bp
     9a0:	8b ec                	mov    %sp,%bp
     9a2:	81 ec 00 00          	sub    $0x0,%sp
     9a6:	57                   	push   %di
     9a7:	56                   	push   %si
     9a8:	8b 46 08             	mov    0x8(%bp),%ax
     9ab:	8b 56 0a             	mov    0xa(%bp),%dx
     9ae:	c4 5e 04             	les    0x4(%bp),%bx
     9b1:	26 8b 5f 4e          	mov    %es:0x4e(%bx),%bx
     9b5:	8b cb                	mov    %bx,%cx
     9b7:	d1 e3                	shl    $1,%bx
     9b9:	d1 e3                	shl    $1,%bx
     9bb:	03 d9                	add    %cx,%bx
     9bd:	d1 e3                	shl    $1,%bx
     9bf:	89 87 22 02          	mov    %ax,0x222(%bx)
     9c3:	89 97 24 02          	mov    %dx,0x224(%bx)
     9c7:	5e                   	pop    %si
     9c8:	5f                   	pop    %di
     9c9:	8b e5                	mov    %bp,%sp
     9cb:	5d                   	pop    %bp
     9cc:	c3                   	ret
     9cd:	55                   	push   %bp
     9ce:	8b ec                	mov    %sp,%bp
     9d0:	81 ec 00 00          	sub    $0x0,%sp
     9d4:	57                   	push   %di
     9d5:	56                   	push   %si
     9d6:	83 7e 08 1a          	cmpw   $0x1a,0x8(%bp)
     9da:	73 03                	jae    0x9df
     9dc:	e9 06 00             	jmp    0x9e5
     9df:	b8 00 00             	mov    $0x0,%ax
     9e2:	e9 8b 00             	jmp    0xa70
     9e5:	c4 5e 04             	les    0x4(%bp),%bx
     9e8:	81 c3 9a 09          	add    $0x99a,%bx
     9ec:	8b 76 08             	mov    0x8(%bp),%si
     9ef:	26 80 38 00          	cmpb   $0x0,%es:(%bx,%si)
     9f3:	75 03                	jne    0x9f8
     9f5:	e9 06 00             	jmp    0x9fe
     9f8:	b8 01 00             	mov    $0x1,%ax
     9fb:	e9 72 00             	jmp    0xa70
     9fe:	b8 44 00             	mov    $0x44,%ax
     a01:	f7 66 08             	mulw   0x8(%bp)
     a04:	8b f0                	mov    %ax,%si
     a06:	c4 5e 04             	les    0x4(%bp),%bx
     a09:	8a 46 08             	mov    0x8(%bp),%al
     a0c:	04 41                	add    $0x41,%al
     a0e:	26 88 80 b4 09       	mov    %al,%es:0x9b4(%bx,%si)
     a13:	b8 44 00             	mov    $0x44,%ax
     a16:	f7 66 08             	mulw   0x8(%bp)
     a19:	8b f0                	mov    %ax,%si
     a1b:	c4 5e 04             	les    0x4(%bp),%bx
     a1e:	26 c6 80 b5 09 3a    	movb   $0x3a,%es:0x9b5(%bx,%si)
     a24:	b8 44 00             	mov    $0x44,%ax
     a27:	f7 66 08             	mulw   0x8(%bp)
     a2a:	8b f0                	mov    %ax,%si
     a2c:	c4 5e 04             	les    0x4(%bp),%bx
     a2f:	26 c6 80 b6 09 5c    	movb   $0x5c,%es:0x9b6(%bx,%si)
     a35:	b8 44 00             	mov    $0x44,%ax
     a38:	f7 66 08             	mulw   0x8(%bp)
     a3b:	03 46 04             	add    0x4(%bp),%ax
     a3e:	8b 56 06             	mov    0x6(%bp),%dx
     a41:	05 b7 09             	add    $0x9b7,%ax
     a44:	52                   	push   %dx
     a45:	50                   	push   %ax
     a46:	8b 46 08             	mov    0x8(%bp),%ax
     a49:	40                   	inc    %ax
     a4a:	50                   	push   %ax
     a4b:	9a ff ff 00 00       	lcall  $0x0,$0xffff
     a50:	3d 00 00             	cmp    $0x0,%ax
     a53:	74 03                	je     0xa58
     a55:	e9 06 00             	jmp    0xa5e
     a58:	b8 00 00             	mov    $0x0,%ax
     a5b:	e9 12 00             	jmp    0xa70
     a5e:	c4 5e 04             	les    0x4(%bp),%bx
     a61:	8b 76 08             	mov    0x8(%bp),%si
     a64:	26 c6 80 9a 09 01    	movb   $0x1,%es:0x99a(%bx,%si)
     a6a:	b8 01 00             	mov    $0x1,%ax
     a6d:	e9 00 00             	jmp    0xa70
     a70:	5e                   	pop    %si
     a71:	5f                   	pop    %di
     a72:	8b e5                	mov    %bp,%sp
     a74:	5d                   	pop    %bp
     a75:	c3                   	ret
     a76:	55                   	push   %bp
     a77:	8b ec                	mov    %sp,%bp
     a79:	81 ec 04 00          	sub    $0x4,%sp
     a7d:	57                   	push   %di
     a7e:	56                   	push   %si
     a7f:	9a f6 0a 00 00       	lcall  $0x0,$0xaf6
     a84:	89 46 fc             	mov    %ax,-0x4(%bp)
     a87:	89 46 fe             	mov    %ax,-0x2(%bp)
     a8a:	c4 5e 08             	les    0x8(%bp),%bx
     a8d:	26 80 3f 00          	cmpb   $0x0,%es:(%bx)
     a91:	75 03                	jne    0xa96
     a93:	e9 2f 00             	jmp    0xac5
     a96:	c4 5e 08             	les    0x8(%bp),%bx
     a99:	26 80 7f 01 3a       	cmpb   $0x3a,%es:0x1(%bx)
     a9e:	74 03                	je     0xaa3
     aa0:	e9 22 00             	jmp    0xac5
     aa3:	c4 5e 08             	les    0x8(%bp),%bx
     aa6:	26 8a 07             	mov    %es:(%bx),%al
     aa9:	50                   	push   %ax
     aaa:	e8 df f7             	call   0x28c
     aad:	83 c4 02             	add    $0x2,%sp
     ab0:	98                   	cbtw
     ab1:	2d 41 00             	sub    $0x41,%ax
     ab4:	89 46 fe             	mov    %ax,-0x2(%bp)
     ab7:	3d 1a 00             	cmp    $0x1a,%ax
     aba:	73 03                	jae    0xabf
     abc:	e9 06 00             	jmp    0xac5
     abf:	b8 00 00             	mov    $0x0,%ax
     ac2:	e9 a1 00             	jmp    0xb66
     ac5:	ff 76 fe             	push   -0x2(%bp)
     ac8:	ff 76 06             	push   0x6(%bp)
     acb:	ff 76 04             	push   0x4(%bp)
     ace:	e8 fc fe             	call   0x9cd
     ad1:	83 c4 06             	add    $0x6,%sp
     ad4:	3d 00 00             	cmp    $0x0,%ax
     ad7:	74 03                	je     0xadc
     ad9:	e9 06 00             	jmp    0xae2
     adc:	b8 00 00             	mov    $0x0,%ax
     adf:	e9 84 00             	jmp    0xb66
     ae2:	8b 46 fc             	mov    -0x4(%bp),%ax
     ae5:	39 46 fe             	cmp    %ax,-0x2(%bp)
     ae8:	75 03                	jne    0xaed
     aea:	e9 1b 00             	jmp    0xb08
     aed:	ff 76 fe             	push   -0x2(%bp)
     af0:	9a 5c 0b 00 00       	lcall  $0x0,$0xb5c
     af5:	9a bd 0b 00 00       	lcall  $0x0,$0xbbd
     afa:	3b 46 fe             	cmp    -0x2(%bp),%ax
     afd:	75 03                	jne    0xb02
     aff:	e9 06 00             	jmp    0xb08
     b02:	b8 00 00             	mov    $0x0,%ax
     b05:	e9 5e 00             	jmp    0xb66
     b08:	c4 5e 08             	les    0x8(%bp),%bx
     b0b:	26 80 3f 00          	cmpb   $0x0,%es:(%bx)
     b0f:	75 03                	jne    0xb14
     b11:	e9 20 00             	jmp    0xb34
     b14:	c4 5e 08             	les    0x8(%bp),%bx
     b17:	26 80 7f 01 3a       	cmpb   $0x3a,%es:0x1(%bx)
     b1c:	74 03                	je     0xb21
     b1e:	e9 13 00             	jmp    0xb34
     b21:	c4 5e 08             	les    0x8(%bp),%bx
     b24:	26 80 7f 02 00       	cmpb   $0x0,%es:0x2(%bx)
     b29:	74 03                	je     0xb2e
     b2b:	e9 06 00             	jmp    0xb34
     b2e:	b8 01 00             	mov    $0x1,%ax
     b31:	e9 32 00             	jmp    0xb66
     b34:	ff 76 0a             	push   0xa(%bp)
     b37:	ff 76 08             	push   0x8(%bp)
     b3a:	9a ff ff 00 00       	lcall  $0x0,$0xffff
     b3f:	3d 00 00             	cmp    $0x0,%ax
     b42:	75 03                	jne    0xb47
     b44:	e9 06 00             	jmp    0xb4d
     b47:	b8 01 00             	mov    $0x1,%ax
     b4a:	e9 19 00             	jmp    0xb66
     b4d:	8b 46 fc             	mov    -0x4(%bp),%ax
     b50:	39 46 fe             	cmp    %ax,-0x2(%bp)
     b53:	75 03                	jne    0xb58
     b55:	e9 08 00             	jmp    0xb60
     b58:	ff 76 fc             	push   -0x4(%bp)
     b5b:	9a b8 0b 00 00       	lcall  $0x0,$0xbb8
     b60:	b8 00 00             	mov    $0x0,%ax
     b63:	e9 00 00             	jmp    0xb66
     b66:	5e                   	pop    %si
     b67:	5f                   	pop    %di
     b68:	8b e5                	mov    %bp,%sp
     b6a:	5d                   	pop    %bp
     b6b:	c3                   	ret
     b6c:	55                   	push   %bp
     b6d:	8b ec                	mov    %sp,%bp
     b6f:	81 ec 04 00          	sub    $0x4,%sp
     b73:	57                   	push   %di
     b74:	56                   	push   %si
     b75:	c7 46 fc 01 00       	movw   $0x1,-0x4(%bp)
     b7a:	c4 5e 04             	les    0x4(%bp),%bx
     b7d:	26 f6 47 34 08       	testb  $0x8,%es:0x34(%bx)
     b82:	74 03                	je     0xb87
     b84:	e9 06 00             	jmp    0xb8d
     b87:	b8 01 00             	mov    $0x1,%ax
     b8a:	e9 8c 00             	jmp    0xc19
     b8d:	c7 46 fe 00 00       	movw   $0x0,-0x2(%bp)
     b92:	e9 03 00             	jmp    0xb98
     b95:	ff 46 fe             	incw   -0x2(%bp)
     b98:	83 7e fe 1a          	cmpw   $0x1a,-0x2(%bp)
     b9c:	72 03                	jb     0xba1
     b9e:	e9 4e 00             	jmp    0xbef
     ba1:	c4 5e 04             	les    0x4(%bp),%bx
     ba4:	81 c3 9a 09          	add    $0x99a,%bx
     ba8:	8b 76 fe             	mov    -0x2(%bp),%si
     bab:	26 80 38 00          	cmpb   $0x0,%es:(%bx,%si)
     baf:	75 03                	jne    0xbb4
     bb1:	e9 38 00             	jmp    0xbec
     bb4:	ff 76 fe             	push   -0x2(%bp)
     bb7:	9a ff ff 00 00       	lcall  $0x0,$0xffff
     bbc:	9a ff ff 00 00       	lcall  $0x0,$0xffff
     bc1:	3b 46 fe             	cmp    -0x2(%bp),%ax
     bc4:	74 03                	je     0xbc9
     bc6:	e9 1e 00             	jmp    0xbe7
     bc9:	b8 44 00             	mov    $0x44,%ax
     bcc:	f7 66 fe             	mulw   -0x2(%bp)
     bcf:	03 46 04             	add    0x4(%bp),%ax
     bd2:	8b 56 06             	mov    0x6(%bp),%dx
     bd5:	05 b4 09             	add    $0x9b4,%ax
     bd8:	52                   	push   %dx
     bd9:	50                   	push   %ax
     bda:	9a 3b 0b 00 00       	lcall  $0x0,$0xb3b
     bdf:	3d 00 00             	cmp    $0x0,%ax
     be2:	74 03                	je     0xbe7
     be4:	e9 05 00             	jmp    0xbec
     be7:	c7 46 fc 00 00       	movw   $0x0,-0x4(%bp)
     bec:	e9 a6 ff             	jmp    0xb95
     bef:	c4 5e 04             	les    0x4(%bp),%bx
     bf2:	26 ff b7 98 09       	push   %es:0x998(%bx)
     bf7:	9a f1 0a 00 00       	lcall  $0x0,$0xaf1
     bfc:	9a 80 0a 00 00       	lcall  $0x0,$0xa80
     c01:	c4 5e 04             	les    0x4(%bp),%bx
     c04:	26 3b 87 98 09       	cmp    %es:0x998(%bx),%ax
     c09:	75 03                	jne    0xc0e
     c0b:	e9 05 00             	jmp    0xc13
     c0e:	c7 46 fc 00 00       	movw   $0x0,-0x4(%bp)
     c13:	8b 46 fc             	mov    -0x4(%bp),%ax
     c16:	e9 00 00             	jmp    0xc19
     c19:	5e                   	pop    %si
     c1a:	5f                   	pop    %di
     c1b:	8b e5                	mov    %bp,%sp
     c1d:	5d                   	pop    %bp
     c1e:	c3                   	ret
     c1f:	55                   	push   %bp
     c20:	8b ec                	mov    %sp,%bp
     c22:	81 ec 0c 00          	sub    $0xc,%sp
     c26:	57                   	push   %di
     c27:	56                   	push   %si
     c28:	c4 5e 04             	les    0x4(%bp),%bx
     c2b:	26 8b 47 0c          	mov    %es:0xc(%bx),%ax
     c2f:	26 8b 57 0e          	mov    %es:0xe(%bx),%dx
     c33:	89 46 fc             	mov    %ax,-0x4(%bp)
     c36:	89 56 fe             	mov    %dx,-0x2(%bp)
     c39:	8b 46 fe             	mov    -0x2(%bp),%ax
     c3c:	0b 46 fc             	or     -0x4(%bp),%ax
     c3f:	74 03                	je     0xc44
     c41:	e9 4e 00             	jmp    0xc92
     c44:	b8 28 00             	mov    $0x28,%ax
     c47:	50                   	push   %ax
     c48:	b8 18 00             	mov    $0x18,%ax
     c4b:	1e                   	push   %ds
     c4c:	50                   	push   %ax
     c4d:	8b 46 04             	mov    0x4(%bp),%ax
     c50:	8b 56 06             	mov    0x6(%bp),%dx
     c53:	05 14 07             	add    $0x714,%ax
     c56:	52                   	push   %dx
     c57:	50                   	push   %ax
     c58:	e8 d1 f5             	call   0x22c
     c5b:	83 c4 0a             	add    $0xa,%sp
     c5e:	b8 40 00             	mov    $0x40,%ax
     c61:	50                   	push   %ax
     c62:	b8 22 00             	mov    $0x22,%ax
     c65:	1e                   	push   %ds
     c66:	50                   	push   %ax
     c67:	8b 46 04             	mov    0x4(%bp),%ax
     c6a:	8b 56 06             	mov    0x6(%bp),%dx
     c6d:	05 14 03             	add    $0x314,%ax
     c70:	52                   	push   %dx
     c71:	50                   	push   %ax
     c72:	e8 b7 f5             	call   0x22c
     c75:	83 c4 0a             	add    $0xa,%sp
     c78:	c4 5e 04             	les    0x4(%bp),%bx
     c7b:	26 c7 87 94 09 01 00 	movw   $0x1,%es:0x994(%bx)
     c82:	c4 5e 04             	les    0x4(%bp),%bx
     c85:	26 c7 87 96 09 00 00 	movw   $0x0,%es:0x996(%bx)
     c8c:	b8 01 00             	mov    $0x1,%ax
     c8f:	e9 f7 01             	jmp    0xe89
     c92:	c7 46 fa 00 00       	movw   $0x0,-0x6(%bp)
     c97:	e9 03 00             	jmp    0xc9d
     c9a:	ff 46 fa             	incw   -0x6(%bp)
     c9d:	83 7e fa 10          	cmpw   $0x10,-0x6(%bp)
     ca1:	72 03                	jb     0xca6
     ca3:	e9 5b 01             	jmp    0xe01
     ca6:	b8 28 00             	mov    $0x28,%ax
     ca9:	50                   	push   %ax
     caa:	ff 76 fe             	push   -0x2(%bp)
     cad:	ff 76 fc             	push   -0x4(%bp)
     cb0:	e8 06 f5             	call   0x1b9
     cb3:	83 c4 06             	add    $0x6,%sp
     cb6:	89 46 f4             	mov    %ax,-0xc(%bp)
     cb9:	3d 28 00             	cmp    $0x28,%ax
     cbc:	74 03                	je     0xcc1
     cbe:	e9 06 00             	jmp    0xcc7
     cc1:	b8 00 00             	mov    $0x0,%ax
     cc4:	e9 c2 01             	jmp    0xe89
     cc7:	83 7e f4 00          	cmpw   $0x0,-0xc(%bp)
     ccb:	74 03                	je     0xcd0
     ccd:	e9 03 00             	jmp    0xcd3
     cd0:	e9 2e 01             	jmp    0xe01
     cd3:	8b 46 f4             	mov    -0xc(%bp),%ax
     cd6:	05 02 00             	add    $0x2,%ax
     cd9:	50                   	push   %ax
     cda:	ff 76 fe             	push   -0x2(%bp)
     cdd:	ff 76 fc             	push   -0x4(%bp)
     ce0:	e8 90 f4             	call   0x173
     ce3:	83 c4 06             	add    $0x6,%sp
     ce6:	3d 00 00             	cmp    $0x0,%ax
     ce9:	74 03                	je     0xcee
     ceb:	e9 06 00             	jmp    0xcf4
     cee:	b8 00 00             	mov    $0x0,%ax
     cf1:	e9 95 01             	jmp    0xe89
     cf4:	b8 28 00             	mov    $0x28,%ax
     cf7:	50                   	push   %ax
     cf8:	ff 76 fe             	push   -0x2(%bp)
     cfb:	ff 76 fc             	push   -0x4(%bp)
     cfe:	f7 66 fa             	mulw   -0x6(%bp)
     d01:	03 46 04             	add    0x4(%bp),%ax
     d04:	8b 56 06             	mov    0x6(%bp),%dx
     d07:	05 14 07             	add    $0x714,%ax
     d0a:	52                   	push   %dx
     d0b:	50                   	push   %ax
     d0c:	e8 1d f5             	call   0x22c
     d0f:	83 c4 0a             	add    $0xa,%sp
     d12:	b8 40 00             	mov    $0x40,%ax
     d15:	50                   	push   %ax
     d16:	8b 4e f4             	mov    -0xc(%bp),%cx
     d19:	41                   	inc    %cx
     d1a:	01 4e fc             	add    %cx,-0x4(%bp)
     d1d:	ff 76 fe             	push   -0x2(%bp)
     d20:	ff 76 fc             	push   -0x4(%bp)
     d23:	e8 93 f4             	call   0x1b9
     d26:	83 c4 06             	add    $0x6,%sp
     d29:	89 46 f4             	mov    %ax,-0xc(%bp)
     d2c:	3d 00 00             	cmp    $0x0,%ax
     d2f:	75 03                	jne    0xd34
     d31:	e9 09 00             	jmp    0xd3d
     d34:	83 7e f4 40          	cmpw   $0x40,-0xc(%bp)
     d38:	74 03                	je     0xd3d
     d3a:	e9 06 00             	jmp    0xd43
     d3d:	b8 00 00             	mov    $0x0,%ax
     d40:	e9 46 01             	jmp    0xe89
     d43:	c7 46 f6 00 00       	movw   $0x0,-0xa(%bp)
     d48:	e9 03 00             	jmp    0xd4e
     d4b:	ff 46 f6             	incw   -0xa(%bp)
     d4e:	8b 46 f4             	mov    -0xc(%bp),%ax
     d51:	39 46 f6             	cmp    %ax,-0xa(%bp)
     d54:	72 03                	jb     0xd59
     d56:	e9 5b 00             	jmp    0xdb4
     d59:	c4 5e fc             	les    -0x4(%bp),%bx
     d5c:	8b 76 f6             	mov    -0xa(%bp),%si
     d5f:	26 8a 00             	mov    %es:(%bx,%si),%al
     d62:	88 46 f8             	mov    %al,-0x8(%bp)
     d65:	3c 5c                	cmp    $0x5c,%al
     d67:	75 03                	jne    0xd6c
     d69:	e9 3f 00             	jmp    0xdab
     d6c:	80 7e f8 2f          	cmpb   $0x2f,-0x8(%bp)
     d70:	75 03                	jne    0xd75
     d72:	e9 36 00             	jmp    0xdab
     d75:	80 7e f8 3a          	cmpb   $0x3a,-0x8(%bp)
     d79:	75 03                	jne    0xd7e
     d7b:	e9 2d 00             	jmp    0xdab
     d7e:	80 7e f8 22          	cmpb   $0x22,-0x8(%bp)
     d82:	75 03                	jne    0xd87
     d84:	e9 24 00             	jmp    0xdab
     d87:	80 7e f8 3c          	cmpb   $0x3c,-0x8(%bp)
     d8b:	75 03                	jne    0xd90
     d8d:	e9 1b 00             	jmp    0xdab
     d90:	80 7e f8 3e          	cmpb   $0x3e,-0x8(%bp)
     d94:	75 03                	jne    0xd99
     d96:	e9 12 00             	jmp    0xdab
     d99:	80 7e f8 7c          	cmpb   $0x7c,-0x8(%bp)
     d9d:	75 03                	jne    0xda2
     d9f:	e9 09 00             	jmp    0xdab
     da2:	80 7e f8 21          	cmpb   $0x21,-0x8(%bp)
     da6:	72 03                	jb     0xdab
     da8:	e9 06 00             	jmp    0xdb1
     dab:	b8 00 00             	mov    $0x0,%ax
     dae:	e9 d8 00             	jmp    0xe89
     db1:	e9 97 ff             	jmp    0xd4b
     db4:	8b 46 f4             	mov    -0xc(%bp),%ax
     db7:	05 02 00             	add    $0x2,%ax
     dba:	50                   	push   %ax
     dbb:	ff 76 fe             	push   -0x2(%bp)
     dbe:	ff 76 fc             	push   -0x4(%bp)
     dc1:	e8 af f3             	call   0x173
     dc4:	83 c4 06             	add    $0x6,%sp
     dc7:	3d 00 00             	cmp    $0x0,%ax
     dca:	74 03                	je     0xdcf
     dcc:	e9 06 00             	jmp    0xdd5
     dcf:	b8 00 00             	mov    $0x0,%ax
     dd2:	e9 b4 00             	jmp    0xe89
     dd5:	b8 40 00             	mov    $0x40,%ax
     dd8:	50                   	push   %ax
     dd9:	ff 76 fe             	push   -0x2(%bp)
     ddc:	ff 76 fc             	push   -0x4(%bp)
     ddf:	b1 06                	mov    $0x6,%cl
     de1:	8b 46 fa             	mov    -0x6(%bp),%ax
     de4:	d3 e0                	shl    %cl,%ax
     de6:	03 46 04             	add    0x4(%bp),%ax
     de9:	8b 56 06             	mov    0x6(%bp),%dx
     dec:	05 14 03             	add    $0x314,%ax
     def:	52                   	push   %dx
     df0:	50                   	push   %ax
     df1:	e8 38 f4             	call   0x22c
     df4:	83 c4 0a             	add    $0xa,%sp
     df7:	8b 46 f4             	mov    -0xc(%bp),%ax
     dfa:	40                   	inc    %ax
     dfb:	01 46 fc             	add    %ax,-0x4(%bp)
     dfe:	e9 99 fe             	jmp    0xc9a
     e01:	83 7e fa 00          	cmpw   $0x0,-0x6(%bp)
     e05:	75 03                	jne    0xe0a
     e07:	e9 15 00             	jmp    0xe1f
     e0a:	83 7e fa 10          	cmpw   $0x10,-0x6(%bp)
     e0e:	74 03                	je     0xe13
     e10:	e9 12 00             	jmp    0xe25
     e13:	c4 5e fc             	les    -0x4(%bp),%bx
     e16:	26 80 3f 00          	cmpb   $0x0,%es:(%bx)
     e1a:	75 03                	jne    0xe1f
     e1c:	e9 06 00             	jmp    0xe25
     e1f:	b8 00 00             	mov    $0x0,%ax
     e22:	e9 64 00             	jmp    0xe89
     e25:	8b 46 fa             	mov    -0x6(%bp),%ax
     e28:	c4 5e 04             	les    0x4(%bp),%bx
     e2b:	26 89 87 94 09       	mov    %ax,%es:0x994(%bx)
     e30:	c4 5e 04             	les    0x4(%bp),%bx
     e33:	26 83 7f 1a 00       	cmpw   $0x0,%es:0x1a(%bx)
     e38:	76 03                	jbe    0xe3d
     e3a:	e9 0a 00             	jmp    0xe47
     e3d:	26 83 7f 18 01       	cmpw   $0x1,%es:0x18(%bx)
     e42:	73 03                	jae    0xe47
     e44:	e9 32 00             	jmp    0xe79
     e47:	8b 46 fa             	mov    -0x6(%bp),%ax
     e4a:	2b d2                	sub    %dx,%dx
     e4c:	c4 5e 04             	les    0x4(%bp),%bx
     e4f:	26 39 57 1a          	cmp    %dx,%es:0x1a(%bx)
     e53:	76 03                	jbe    0xe58
     e55:	e9 21 00             	jmp    0xe79
     e58:	73 03                	jae    0xe5d
     e5a:	e9 09 00             	jmp    0xe66
     e5d:	26 39 47 18          	cmp    %ax,%es:0x18(%bx)
     e61:	76 03                	jbe    0xe66
     e63:	e9 13 00             	jmp    0xe79
     e66:	c4 5e 04             	les    0x4(%bp),%bx
     e69:	26 8b 47 18          	mov    %es:0x18(%bx),%ax
     e6d:	48                   	dec    %ax
     e6e:	c4 5e 04             	les    0x4(%bp),%bx
     e71:	26 89 87 96 09       	mov    %ax,%es:0x996(%bx)
     e76:	e9 0a 00             	jmp    0xe83
     e79:	c4 5e 04             	les    0x4(%bp),%bx
     e7c:	26 c7 87 96 09 00 00 	movw   $0x0,%es:0x996(%bx)
     e83:	b8 01 00             	mov    $0x1,%ax
     e86:	e9 00 00             	jmp    0xe89
     e89:	5e                   	pop    %si
     e8a:	5f                   	pop    %di
     e8b:	8b e5                	mov    %bp,%sp
     e8d:	5d                   	pop    %bp
     e8e:	c3                   	ret
     e8f:	55                   	push   %bp
     e90:	8b ec                	mov    %sp,%bp
     e92:	81 ec 00 00          	sub    $0x0,%sp
     e96:	57                   	push   %di
     e97:	56                   	push   %si
     e98:	ff 76 08             	push   0x8(%bp)
     e9b:	ff 76 06             	push   0x6(%bp)
     e9e:	ff 76 0c             	push   0xc(%bp)
     ea1:	ff 76 0a             	push   0xa(%bp)
     ea4:	8b 46 0e             	mov    0xe(%bp),%ax
     ea7:	8b 56 10             	mov    0x10(%bp),%dx
     eaa:	0d 00 00             	or     $0x0,%ax
     ead:	81 ca 00 50          	or     $0x5000,%dx
     eb1:	52                   	push   %dx
     eb2:	50                   	push   %ax
     eb3:	ff 76 12             	push   0x12(%bp)
     eb6:	ff 76 14             	push   0x14(%bp)
     eb9:	ff 76 16             	push   0x16(%bp)
     ebc:	ff 76 18             	push   0x18(%bp)
     ebf:	ff 76 04             	push   0x4(%bp)
     ec2:	ff 76 1a             	push   0x1a(%bp)
     ec5:	ff 36 1e 02          	push   0x21e
     ec9:	2b c0                	sub    %ax,%ax
     ecb:	50                   	push   %ax
     ecc:	50                   	push   %ax
     ecd:	9a ff ff 00 00       	lcall  $0x0,$0xffff
     ed2:	e9 00 00             	jmp    0xed5
     ed5:	5e                   	pop    %si
     ed6:	5f                   	pop    %di
     ed7:	8b e5                	mov    %bp,%sp
     ed9:	5d                   	pop    %bp
     eda:	c3                   	ret
     edb:	55                   	push   %bp
     edc:	8b ec                	mov    %sp,%bp
     ede:	81 ec 3a 00          	sub    $0x3a,%sp
     ee2:	57                   	push   %di
     ee3:	56                   	push   %si
     ee4:	b8 00 00             	mov    $0x0,%ax
     ee7:	50                   	push   %ax
     ee8:	9a f5 0e 00 00       	lcall  $0x0,$0xef5
     eed:	89 46 ce             	mov    %ax,-0x32(%bp)
     ef0:	b8 01 00             	mov    $0x1,%ax
     ef3:	50                   	push   %ax
     ef4:	9a ff ff 00 00       	lcall  $0x0,$0xffff
     ef9:	89 46 ca             	mov    %ax,-0x36(%bp)
     efc:	81 7e ce c8 00       	cmpw   $0xc8,-0x32(%bp)
     f01:	7d 03                	jge    0xf06
     f03:	e9 16 00             	jmp    0xf1c
     f06:	81 7e ce 90 01       	cmpw   $0x190,-0x32(%bp)
     f0b:	7d 03                	jge    0xf10
     f0d:	e9 06 00             	jmp    0xf16
     f10:	b8 88 01             	mov    $0x188,%ax
     f13:	e9 03 00             	jmp    0xf19
     f16:	b8 24 01             	mov    $0x124,%ax
     f19:	e9 03 00             	jmp    0xf1f
     f1c:	8b 46 ce             	mov    -0x32(%bp),%ax
     f1f:	89 46 c6             	mov    %ax,-0x3a(%bp)
     f22:	ff 76 04             	push   0x4(%bp)
     f25:	9a ff ff 00 00       	lcall  $0x0,$0xffff
     f2a:	89 46 d6             	mov    %ax,-0x2a(%bp)
     f2d:	3d 00 00             	cmp    $0x0,%ax
     f30:	74 03                	je     0xf35
     f32:	e9 06 00             	jmp    0xf3b
     f35:	b8 00 00             	mov    $0x0,%ax
     f38:	e9 9c 03             	jmp    0x12d7
     f3b:	ff 76 d6             	push   -0x2a(%bp)
     f3e:	8d 46 e0             	lea    -0x20(%bp),%ax
     f41:	16                   	push   %ss
     f42:	50                   	push   %ax
     f43:	9a ff ff 00 00       	lcall  $0x0,$0xffff
     f48:	3d 00 00             	cmp    $0x0,%ax
     f4b:	74 03                	je     0xf50
     f4d:	e9 11 00             	jmp    0xf61
     f50:	ff 76 04             	push   0x4(%bp)
     f53:	ff 76 d6             	push   -0x2a(%bp)
     f56:	9a 68 0f 00 00       	lcall  $0x0,$0xf68
     f5b:	b8 00 00             	mov    $0x0,%ax
     f5e:	e9 76 03             	jmp    0x12d7
     f61:	ff 76 04             	push   0x4(%bp)
     f64:	ff 76 d6             	push   -0x2a(%bp)
     f67:	9a ff ff 00 00       	lcall  $0x0,$0xffff
     f6c:	8b 46 e0             	mov    -0x20(%bp),%ax
     f6f:	89 46 c8             	mov    %ax,-0x38(%bp)
     f72:	3d 01 00             	cmp    $0x1,%ax
     f75:	7d 03                	jge    0xf7a
     f77:	e9 09 00             	jmp    0xf83
     f7a:	83 7e c8 18          	cmpw   $0x18,-0x38(%bp)
     f7e:	7f 03                	jg     0xf83
     f80:	e9 06 00             	jmp    0xf89
     f83:	b8 00 00             	mov    $0x0,%ax
     f86:	e9 4e 03             	jmp    0x12d7
     f89:	b8 04 00             	mov    $0x4,%ax
     f8c:	50                   	push   %ax
     f8d:	9a 99 0f 00 00       	lcall  $0x0,$0xf99
     f92:	b9 08 00             	mov    $0x8,%cx
     f95:	51                   	push   %cx
     f96:	8b f0                	mov    %ax,%si
     f98:	9a e9 0e 00 00       	lcall  $0x0,$0xee9
     f9d:	2d fd ff             	sub    $0xfffd,%ax
     fa0:	f7 d8                	neg    %ax
     fa2:	d1 e0                	shl    $1,%ax
     fa4:	2b c6                	sub    %si,%ax
     fa6:	03 46 ca             	add    -0x36(%bp),%ax
     fa9:	89 46 cc             	mov    %ax,-0x34(%bp)
     fac:	ff 76 04             	push   0x4(%bp)
     faf:	8b 46 ce             	mov    -0x32(%bp),%ax
     fb2:	2b 46 c6             	sub    -0x3a(%bp),%ax
     fb5:	99                   	cwtd
     fb6:	2b c2                	sub    %dx,%ax
     fb8:	d1 f8                	sar    $1,%ax
     fba:	50                   	push   %ax
     fbb:	b8 01 00             	mov    $0x1,%ax
     fbe:	50                   	push   %ax
     fbf:	ff 76 c6             	push   -0x3a(%bp)
     fc2:	8b 46 ca             	mov    -0x36(%bp),%ax
     fc5:	2d 02 00             	sub    $0x2,%ax
     fc8:	50                   	push   %ax
     fc9:	b8 00 00             	mov    $0x0,%ax
     fcc:	50                   	push   %ax
     fcd:	9a ff ff 00 00       	lcall  $0x0,$0xffff
     fd2:	ff 76 04             	push   0x4(%bp)
     fd5:	8d 46 d8             	lea    -0x28(%bp),%ax
     fd8:	16                   	push   %ss
     fd9:	50                   	push   %ax
     fda:	9a ff ff 00 00       	lcall  $0x0,$0xffff
     fdf:	8b 46 dc             	mov    -0x24(%bp),%ax
     fe2:	89 46 c6             	mov    %ax,-0x3a(%bp)
     fe5:	8b 46 c8             	mov    -0x38(%bp),%ax
     fe8:	8b c8                	mov    %ax,%cx
     fea:	d1 e0                	shl    $1,%ax
     fec:	03 c1                	add    %cx,%ax
     fee:	d1 e0                	shl    $1,%ax
     ff0:	05 25 00             	add    $0x25,%ax
     ff3:	8b 4e de             	mov    -0x22(%bp),%cx
     ff6:	89 4e cc             	mov    %cx,-0x34(%bp)
     ff9:	3b c1                	cmp    %cx,%ax
     ffb:	7f 03                	jg     0x1000
     ffd:	e9 06 00             	jmp    0x1006
    1000:	b8 00 00             	mov    $0x0,%ax
    1003:	e9 d1 02             	jmp    0x12d7
    1006:	c7 46 d0 02 00       	movw   $0x2,-0x30(%bp)
    100b:	b8 69 00             	mov    $0x69,%ax
    100e:	50                   	push   %ax
    100f:	ff 76 c8             	push   -0x38(%bp)
    1012:	8b 46 c6             	mov    -0x3a(%bp),%ax
    1015:	2d 06 00             	sub    $0x6,%ax
    1018:	50                   	push   %ax
    1019:	ff 76 d0             	push   -0x30(%bp)
    101c:	b8 03 00             	mov    $0x3,%ax
    101f:	50                   	push   %ax
    1020:	2b c0                	sub    %ax,%ax
    1022:	50                   	push   %ax
    1023:	50                   	push   %ax
    1024:	b8 26 00             	mov    $0x26,%ax
    1027:	1e                   	push   %ds
    1028:	50                   	push   %ax
    1029:	b8 2d 00             	mov    $0x2d,%ax
    102c:	1e                   	push   %ds
    102d:	50                   	push   %ax
    102e:	ff 76 04             	push   0x4(%bp)
    1031:	e8 5b fe             	call   0xe8f
    1034:	83 c4 18             	add    $0x18,%sp
    1037:	3d 00 00             	cmp    $0x0,%ax
    103a:	74 03                	je     0x103f
    103c:	e9 06 00             	jmp    0x1045
    103f:	b8 00 00             	mov    $0x0,%ax
    1042:	e9 92 02             	jmp    0x12d7
    1045:	8b 46 c8             	mov    -0x38(%bp),%ax
    1048:	01 46 d0             	add    %ax,-0x30(%bp)
    104b:	b8 64 00             	mov    $0x64,%ax
    104e:	50                   	push   %ax
    104f:	8b 46 c8             	mov    -0x38(%bp),%ax
    1052:	05 04 00             	add    $0x4,%ax
    1055:	50                   	push   %ax
    1056:	8b 46 c6             	mov    -0x3a(%bp),%ax
    1059:	2d 06 00             	sub    $0x6,%ax
    105c:	50                   	push   %ax
    105d:	ff 76 d0             	push   -0x30(%bp)
    1060:	b8 03 00             	mov    $0x3,%ax
    1063:	50                   	push   %ax
    1064:	b8 80 00             	mov    $0x80,%ax
    1067:	ba 81 00             	mov    $0x81,%dx
    106a:	52                   	push   %dx
    106b:	50                   	push   %ax
    106c:	8b 46 06             	mov    0x6(%bp),%ax
    106f:	8b 56 08             	mov    0x8(%bp),%dx
    1072:	05 50 00             	add    $0x50,%ax
    1075:	52                   	push   %dx
    1076:	50                   	push   %ax
    1077:	b8 34 00             	mov    $0x34,%ax
    107a:	1e                   	push   %ds
    107b:	50                   	push   %ax
    107c:	ff 76 04             	push   0x4(%bp)
    107f:	e8 0d fe             	call   0xe8f
    1082:	83 c4 18             	add    $0x18,%sp
    1085:	89 46 d4             	mov    %ax,-0x2c(%bp)
    1088:	3d 00 00             	cmp    $0x0,%ax
    108b:	74 03                	je     0x1090
    108d:	e9 06 00             	jmp    0x1096
    1090:	b8 00 00             	mov    $0x0,%ax
    1093:	e9 41 02             	jmp    0x12d7
    1096:	ff 76 d4             	push   -0x2c(%bp)
    1099:	b8 15 04             	mov    $0x415,%ax
    109c:	50                   	push   %ax
    109d:	b8 7f 00             	mov    $0x7f,%ax
    10a0:	50                   	push   %ax
    10a1:	2b c0                	sub    %ax,%ax
    10a3:	50                   	push   %ax
    10a4:	50                   	push   %ax
    10a5:	9a 21 12 00 00       	lcall  $0x0,$0x1221
    10aa:	8b 46 c8             	mov    -0x38(%bp),%ax
    10ad:	05 05 00             	add    $0x5,%ax
    10b0:	01 46 d0             	add    %ax,-0x30(%bp)
    10b3:	b8 67 00             	mov    $0x67,%ax
    10b6:	50                   	push   %ax
    10b7:	ff 76 c8             	push   -0x38(%bp)
    10ba:	8b 46 c6             	mov    -0x3a(%bp),%ax
    10bd:	2d 06 00             	sub    $0x6,%ax
    10c0:	50                   	push   %ax
    10c1:	ff 76 d0             	push   -0x30(%bp)
    10c4:	b8 03 00             	mov    $0x3,%ax
    10c7:	50                   	push   %ax
    10c8:	2b c0                	sub    %ax,%ax
    10ca:	50                   	push   %ax
    10cb:	50                   	push   %ax
    10cc:	b8 39 00             	mov    $0x39,%ax
    10cf:	1e                   	push   %ds
    10d0:	50                   	push   %ax
    10d1:	b8 3a 00             	mov    $0x3a,%ax
    10d4:	1e                   	push   %ds
    10d5:	50                   	push   %ax
    10d6:	ff 76 04             	push   0x4(%bp)
    10d9:	e8 b3 fd             	call   0xe8f
    10dc:	83 c4 18             	add    $0x18,%sp
    10df:	3d 00 00             	cmp    $0x0,%ax
    10e2:	74 03                	je     0x10e7
    10e4:	e9 06 00             	jmp    0x10ed
    10e7:	b8 00 00             	mov    $0x0,%ax
    10ea:	e9 ea 01             	jmp    0x12d7
    10ed:	8b 46 c8             	mov    -0x38(%bp),%ax
    10f0:	40                   	inc    %ax
    10f1:	01 46 d0             	add    %ax,-0x30(%bp)
    10f4:	b8 65 00             	mov    $0x65,%ax
    10f7:	50                   	push   %ax
    10f8:	b8 f9 ff             	mov    $0xfff9,%ax
    10fb:	2b 46 c8             	sub    -0x38(%bp),%ax
    10fe:	8b c8                	mov    %ax,%cx
    1100:	d1 e0                	shl    $1,%ax
    1102:	03 c1                	add    %cx,%ax
    1104:	2b 46 d0             	sub    -0x30(%bp),%ax
    1107:	03 46 cc             	add    -0x34(%bp),%ax
    110a:	50                   	push   %ax
    110b:	8b 46 c6             	mov    -0x3a(%bp),%ax
    110e:	2d 06 00             	sub    $0x6,%ax
    1111:	50                   	push   %ax
    1112:	ff 76 d0             	push   -0x30(%bp)
    1115:	b8 03 00             	mov    $0x3,%ax
    1118:	50                   	push   %ax
    1119:	b8 03 00             	mov    $0x3,%ax
    111c:	ba a1 00             	mov    $0xa1,%dx
    111f:	52                   	push   %dx
    1120:	50                   	push   %ax
    1121:	b8 41 00             	mov    $0x41,%ax
    1124:	1e                   	push   %ds
    1125:	50                   	push   %ax
    1126:	b8 42 00             	mov    $0x42,%ax
    1129:	1e                   	push   %ds
    112a:	50                   	push   %ax
    112b:	ff 76 04             	push   0x4(%bp)
    112e:	e8 5e fd             	call   0xe8f
    1131:	83 c4 18             	add    $0x18,%sp
    1134:	3d 00 00             	cmp    $0x0,%ax
    1137:	74 03                	je     0x113c
    1139:	e9 06 00             	jmp    0x1142
    113c:	b8 00 00             	mov    $0x0,%ax
    113f:	e9 95 01             	jmp    0x12d7
    1142:	8b 46 c8             	mov    -0x38(%bp),%ax
    1145:	8b c8                	mov    %ax,%cx
    1147:	d1 e0                	shl    $1,%ax
    1149:	03 c1                	add    %cx,%ax
    114b:	2b 46 cc             	sub    -0x34(%bp),%ax
    114e:	f7 d8                	neg    %ax
    1150:	2d 13 00             	sub    $0x13,%ax
    1153:	89 46 d0             	mov    %ax,-0x30(%bp)
    1156:	b8 66 00             	mov    $0x66,%ax
    1159:	50                   	push   %ax
    115a:	8b 46 c8             	mov    -0x38(%bp),%ax
    115d:	8b c8                	mov    %ax,%cx
    115f:	d1 e0                	shl    $1,%ax
    1161:	03 c1                	add    %cx,%ax
    1163:	d1 e0                	shl    $1,%ax
    1165:	50                   	push   %ax
    1166:	8b 46 c6             	mov    -0x3a(%bp),%ax
    1169:	2d 06 00             	sub    $0x6,%ax
    116c:	50                   	push   %ax
    116d:	ff 76 d0             	push   -0x30(%bp)
    1170:	b8 03 00             	mov    $0x3,%ax
    1173:	50                   	push   %ax
    1174:	b8 03 00             	mov    $0x3,%ax
    1177:	ba 21 00             	mov    $0x21,%dx
    117a:	52                   	push   %dx
    117b:	50                   	push   %ax
    117c:	b8 4a 00             	mov    $0x4a,%ax
    117f:	1e                   	push   %ds
    1180:	50                   	push   %ax
    1181:	b8 4b 00             	mov    $0x4b,%ax
    1184:	1e                   	push   %ds
    1185:	50                   	push   %ax
    1186:	ff 76 04             	push   0x4(%bp)
    1189:	e8 03 fd             	call   0xe8f
    118c:	83 c4 18             	add    $0x18,%sp
    118f:	3d 00 00             	cmp    $0x0,%ax
    1192:	74 03                	je     0x1197
    1194:	e9 06 00             	jmp    0x119d
    1197:	b8 00 00             	mov    $0x0,%ax
    119a:	e9 3a 01             	jmp    0x12d7
    119d:	8b 46 c8             	mov    -0x38(%bp),%ax
    11a0:	05 06 00             	add    $0x6,%ax
    11a3:	01 46 d0             	add    %ax,-0x30(%bp)
    11a6:	b8 68 00             	mov    $0x68,%ax
    11a9:	50                   	push   %ax
    11aa:	8b 46 c8             	mov    -0x38(%bp),%ax
    11ad:	05 03 00             	add    $0x3,%ax
    11b0:	50                   	push   %ax
    11b1:	8b 46 c6             	mov    -0x3a(%bp),%ax
    11b4:	2d 06 00             	sub    $0x6,%ax
    11b7:	50                   	push   %ax
    11b8:	ff 76 d0             	push   -0x30(%bp)
    11bb:	b8 03 00             	mov    $0x3,%ax
    11be:	50                   	push   %ax
    11bf:	b8 03 00             	mov    $0x3,%ax
    11c2:	ba 01 00             	mov    $0x1,%dx
    11c5:	52                   	push   %dx
    11c6:	50                   	push   %ax
    11c7:	b8 54 00             	mov    $0x54,%ax
    11ca:	1e                   	push   %ds
    11cb:	50                   	push   %ax
    11cc:	b8 5f 00             	mov    $0x5f,%ax
    11cf:	1e                   	push   %ds
    11d0:	50                   	push   %ax
    11d1:	ff 76 04             	push   0x4(%bp)
    11d4:	e8 b8 fc             	call   0xe8f
    11d7:	83 c4 18             	add    $0x18,%sp
    11da:	89 46 d4             	mov    %ax,-0x2c(%bp)
    11dd:	3d 00 00             	cmp    $0x0,%ax
    11e0:	74 03                	je     0x11e5
    11e2:	e9 06 00             	jmp    0x11eb
    11e5:	b8 00 00             	mov    $0x0,%ax
    11e8:	e9 ec 00             	jmp    0x12d7
    11eb:	c4 5e 06             	les    0x6(%bp),%bx
    11ee:	26 f6 47 34 04       	testb  $0x4,%es:0x34(%bx)
    11f3:	75 03                	jne    0x11f8
    11f5:	e9 0c 00             	jmp    0x1204
    11f8:	ff 76 d4             	push   -0x2c(%bp)
    11fb:	b8 00 00             	mov    $0x0,%ax
    11fe:	50                   	push   %ax
    11ff:	9a ff ff 00 00       	lcall  $0x0,$0xffff
    1204:	c4 5e 06             	les    0x6(%bp),%bx
    1207:	26 f6 47 34 01       	testb  $0x1,%es:0x34(%bx)
    120c:	75 03                	jne    0x1211
    120e:	e9 14 00             	jmp    0x1225
    1211:	ff 76 d4             	push   -0x2c(%bp)
    1214:	b8 01 04             	mov    $0x401,%ax
    1217:	50                   	push   %ax
    1218:	b8 01 00             	mov    $0x1,%ax
    121b:	50                   	push   %ax
    121c:	2b c0                	sub    %ax,%ax
    121e:	50                   	push   %ax
    121f:	50                   	push   %ax
    1220:	9a ff ff 00 00       	lcall  $0x0,$0xffff
    1225:	8b 46 cc             	mov    -0x34(%bp),%ax
    1228:	2b 46 c8             	sub    -0x38(%bp),%ax
    122b:	2d 05 00             	sub    $0x5,%ax
    122e:	89 46 d0             	mov    %ax,-0x30(%bp)
    1231:	8b 46 c6             	mov    -0x3a(%bp),%ax
    1234:	2d 09 00             	sub    $0x9,%ax
    1237:	99                   	cwtd
    1238:	2b c2                	sub    %dx,%ax
    123a:	d1 f8                	sar    $1,%ax
    123c:	89 46 d2             	mov    %ax,-0x2e(%bp)
    123f:	b8 01 00             	mov    $0x1,%ax
    1242:	50                   	push   %ax
    1243:	8b 46 c8             	mov    -0x38(%bp),%ax
    1246:	05 04 00             	add    $0x4,%ax
    1249:	50                   	push   %ax
    124a:	ff 76 d2             	push   -0x2e(%bp)
    124d:	ff 76 d0             	push   -0x30(%bp)
    1250:	b8 03 00             	mov    $0x3,%ax
    1253:	50                   	push   %ax
    1254:	b8 01 00             	mov    $0x1,%ax
    1257:	ba 01 00             	mov    $0x1,%dx
    125a:	52                   	push   %dx
    125b:	50                   	push   %ax
    125c:	c4 5e 06             	les    0x6(%bp),%bx
    125f:	26 83 7f 4c 00       	cmpw   $0x0,%es:0x4c(%bx)
    1264:	75 03                	jne    0x1269
    1266:	e9 06 00             	jmp    0x126f
    1269:	b8 66 00             	mov    $0x66,%ax
    126c:	e9 03 00             	jmp    0x1272
    126f:	b8 6c 00             	mov    $0x6c,%ax
    1272:	1e                   	push   %ds
    1273:	50                   	push   %ax
    1274:	b8 72 00             	mov    $0x72,%ax
    1277:	1e                   	push   %ds
    1278:	50                   	push   %ax
    1279:	ff 76 04             	push   0x4(%bp)
    127c:	e8 10 fc             	call   0xe8f
    127f:	83 c4 18             	add    $0x18,%sp
    1282:	3d 00 00             	cmp    $0x0,%ax
    1285:	74 03                	je     0x128a
    1287:	e9 06 00             	jmp    0x1290
    128a:	b8 00 00             	mov    $0x0,%ax
    128d:	e9 47 00             	jmp    0x12d7
    1290:	b8 02 00             	mov    $0x2,%ax
    1293:	50                   	push   %ax
    1294:	8b 46 c8             	mov    -0x38(%bp),%ax
    1297:	05 04 00             	add    $0x4,%ax
    129a:	50                   	push   %ax
    129b:	ff 76 d2             	push   -0x2e(%bp)
    129e:	ff 76 d0             	push   -0x30(%bp)
    12a1:	8b 46 d2             	mov    -0x2e(%bp),%ax
    12a4:	05 06 00             	add    $0x6,%ax
    12a7:	50                   	push   %ax
    12a8:	b8 00 00             	mov    $0x0,%ax
    12ab:	ba 01 00             	mov    $0x1,%dx
    12ae:	52                   	push   %dx
    12af:	50                   	push   %ax
    12b0:	b8 79 00             	mov    $0x79,%ax
    12b3:	1e                   	push   %ds
    12b4:	50                   	push   %ax
    12b5:	b8 80 00             	mov    $0x80,%ax
    12b8:	1e                   	push   %ds
    12b9:	50                   	push   %ax
    12ba:	ff 76 04             	push   0x4(%bp)
    12bd:	e8 cf fb             	call   0xe8f
    12c0:	83 c4 18             	add    $0x18,%sp
    12c3:	3d 00 00             	cmp    $0x0,%ax
    12c6:	74 03                	je     0x12cb
    12c8:	e9 06 00             	jmp    0x12d1
    12cb:	b8 00 00             	mov    $0x0,%ax
    12ce:	e9 06 00             	jmp    0x12d7
    12d1:	b8 01 00             	mov    $0x1,%ax
    12d4:	e9 00 00             	jmp    0x12d7
    12d7:	5e                   	pop    %si
    12d8:	5f                   	pop    %di
    12d9:	8b e5                	mov    %bp,%sp
    12db:	5d                   	pop    %bp
    12dc:	c3                   	ret
    12dd:	55                   	push   %bp
    12de:	8b ec                	mov    %sp,%bp
    12e0:	81 ec 08 00          	sub    $0x8,%sp
    12e4:	57                   	push   %di
    12e5:	56                   	push   %si
    12e6:	b1 06                	mov    $0x6,%cl
    12e8:	c4 5e 06             	les    0x6(%bp),%bx
    12eb:	26 8b 87 96 09       	mov    %es:0x996(%bx),%ax
    12f0:	d3 e0                	shl    %cl,%ax
    12f2:	03 46 06             	add    0x6(%bp),%ax
    12f5:	8b 56 08             	mov    0x8(%bp),%dx
    12f8:	05 14 03             	add    $0x314,%ax
    12fb:	89 46 fc             	mov    %ax,-0x4(%bp)
    12fe:	89 56 fe             	mov    %dx,-0x2(%bp)
    1301:	b8 80 00             	mov    $0x80,%ax
    1304:	50                   	push   %ax
    1305:	b8 87 00             	mov    $0x87,%ax
    1308:	1e                   	push   %ds
    1309:	50                   	push   %ax
    130a:	8b 46 06             	mov    0x6(%bp),%ax
    130d:	8b 56 08             	mov    0x8(%bp),%dx
    1310:	05 50 01             	add    $0x150,%ax
    1313:	52                   	push   %dx
    1314:	50                   	push   %ax
    1315:	e8 14 ef             	call   0x22c
    1318:	83 c4 0a             	add    $0xa,%sp
    131b:	ff 76 04             	push   0x4(%bp)
    131e:	8b 46 06             	mov    0x6(%bp),%ax
    1321:	8b 56 08             	mov    0x8(%bp),%dx
    1324:	05 50 01             	add    $0x150,%ax
    1327:	52                   	push   %dx
    1328:	50                   	push   %ax
    1329:	b8 65 00             	mov    $0x65,%ax
    132c:	50                   	push   %ax
    132d:	b8 67 00             	mov    $0x67,%ax
    1330:	50                   	push   %ax
    1331:	b8 10 c0             	mov    $0xc010,%ax
    1334:	50                   	push   %ax
    1335:	9a ff ff 00 00       	lcall  $0x0,$0xffff
    133a:	c4 5e fc             	les    -0x4(%bp),%bx
    133d:	26 80 3f 00          	cmpb   $0x0,%es:(%bx)
    1341:	75 03                	jne    0x1346
    1343:	e9 89 00             	jmp    0x13cf
    1346:	c7 46 f8 00 00       	movw   $0x0,-0x8(%bp)
    134b:	e9 03 00             	jmp    0x1351
    134e:	ff 46 f8             	incw   -0x8(%bp)
    1351:	c4 5e fc             	les    -0x4(%bp),%bx
    1354:	26 80 3f 00          	cmpb   $0x0,%es:(%bx)
    1358:	75 03                	jne    0x135d
    135a:	e9 2c 00             	jmp    0x1389
    135d:	c4 5e fc             	les    -0x4(%bp),%bx
    1360:	26 80 3f 3b          	cmpb   $0x3b,%es:(%bx)
    1364:	75 03                	jne    0x1369
    1366:	e9 20 00             	jmp    0x1389
    1369:	83 7e f8 7f          	cmpw   $0x7f,-0x8(%bp)
    136d:	72 03                	jb     0x1372
    136f:	e9 17 00             	jmp    0x1389
    1372:	c4 5e fc             	les    -0x4(%bp),%bx
    1375:	ff 46 fc             	incw   -0x4(%bp)
    1378:	26 8a 07             	mov    %es:(%bx),%al
    137b:	c4 5e 06             	les    0x6(%bp),%bx
    137e:	8b 76 f8             	mov    -0x8(%bp),%si
    1381:	26 88 80 50 01       	mov    %al,%es:0x150(%bx,%si)
    1386:	e9 c5 ff             	jmp    0x134e
    1389:	c4 5e 06             	les    0x6(%bp),%bx
    138c:	8b 76 f8             	mov    -0x8(%bp),%si
    138f:	26 c6 80 50 01 00    	movb   $0x0,%es:0x150(%bx,%si)
    1395:	c4 5e fc             	les    -0x4(%bp),%bx
    1398:	26 80 3f 3b          	cmpb   $0x3b,%es:(%bx)
    139c:	74 03                	je     0x13a1
    139e:	e9 03 00             	jmp    0x13a4
    13a1:	ff 46 fc             	incw   -0x4(%bp)
    13a4:	83 7e f8 00          	cmpw   $0x0,-0x8(%bp)
    13a8:	75 03                	jne    0x13ad
    13aa:	e9 1f 00             	jmp    0x13cc
    13ad:	ff 76 04             	push   0x4(%bp)
    13b0:	b8 65 00             	mov    $0x65,%ax
    13b3:	50                   	push   %ax
    13b4:	b8 0e 04             	mov    $0x40e,%ax
    13b7:	50                   	push   %ax
    13b8:	b8 21 00             	mov    $0x21,%ax
    13bb:	50                   	push   %ax
    13bc:	8b 46 06             	mov    0x6(%bp),%ax
    13bf:	8b 56 08             	mov    0x8(%bp),%dx
    13c2:	05 50 01             	add    $0x150,%ax
    13c5:	52                   	push   %dx
    13c6:	50                   	push   %ax
    13c7:	9a ff ff 00 00       	lcall  $0x0,$0xffff
    13cc:	e9 6b ff             	jmp    0x133a
    13cf:	c7 46 fa 00 00       	movw   $0x0,-0x6(%bp)
    13d4:	e9 03 00             	jmp    0x13da
    13d7:	ff 46 fa             	incw   -0x6(%bp)
    13da:	81 7e fa 80 00       	cmpw   $0x80,-0x6(%bp)
    13df:	72 03                	jb     0x13e4
    13e1:	e9 0f 00             	jmp    0x13f3
    13e4:	c4 5e 06             	les    0x6(%bp),%bx
    13e7:	8b 76 fa             	mov    -0x6(%bp),%si
    13ea:	26 c6 80 50 01 00    	movb   $0x0,%es:0x150(%bx,%si)
    13f0:	e9 e4 ff             	jmp    0x13d7
    13f3:	5e                   	pop    %si
    13f4:	5f                   	pop    %di
    13f5:	8b e5                	mov    %bp,%sp
    13f7:	5d                   	pop    %bp
    13f8:	c3                   	ret
    13f9:	55                   	push   %bp
    13fa:	8b ec                	mov    %sp,%bp
    13fc:	81 ec 02 00          	sub    $0x2,%sp
    1400:	57                   	push   %di
    1401:	56                   	push   %si
    1402:	c7 46 fe 00 00       	movw   $0x0,-0x2(%bp)
    1407:	e9 03 00             	jmp    0x140d
    140a:	ff 46 fe             	incw   -0x2(%bp)
    140d:	c4 5e 04             	les    0x4(%bp),%bx
    1410:	8b 76 fe             	mov    -0x2(%bp),%si
    1413:	26 80 38 00          	cmpb   $0x0,%es:(%bx,%si)
    1417:	75 03                	jne    0x141c
    1419:	e9 27 00             	jmp    0x1443
    141c:	c4 5e 04             	les    0x4(%bp),%bx
    141f:	8b 76 fe             	mov    -0x2(%bp),%si
    1422:	26 80 38 2a          	cmpb   $0x2a,%es:(%bx,%si)
    1426:	75 03                	jne    0x142b
    1428:	e9 0f 00             	jmp    0x143a
    142b:	c4 5e 04             	les    0x4(%bp),%bx
    142e:	8b 76 fe             	mov    -0x2(%bp),%si
    1431:	26 80 38 3f          	cmpb   $0x3f,%es:(%bx,%si)
    1435:	74 03                	je     0x143a
    1437:	e9 06 00             	jmp    0x1440
    143a:	b8 01 00             	mov    $0x1,%ax
    143d:	e9 09 00             	jmp    0x1449
    1440:	e9 c7 ff             	jmp    0x140a
    1443:	b8 00 00             	mov    $0x0,%ax
    1446:	e9 00 00             	jmp    0x1449
    1449:	5e                   	pop    %si
    144a:	5f                   	pop    %di
    144b:	8b e5                	mov    %bp,%sp
    144d:	5d                   	pop    %bp
    144e:	c3                   	ret
    144f:	1e                   	push   %ds
    1450:	58                   	pop    %ax
    1451:	90                   	nop
    1452:	45                   	inc    %bp
    1453:	55                   	push   %bp
    1454:	8b ec                	mov    %sp,%bp
    1456:	1e                   	push   %ds
    1457:	8e d8                	mov    %ax,%ds
    1459:	81 ec 3c 00          	sub    $0x3c,%sp
    145d:	57                   	push   %di
    145e:	56                   	push   %si
    145f:	81 7e 0c 10 01       	cmpw   $0x110,0xc(%bp)
    1464:	74 03                	je     0x1469
    1466:	e9 53 00             	jmp    0x14bc
    1469:	e8 42 ec             	call   0xae
    146c:	89 46 cc             	mov    %ax,-0x34(%bp)
    146f:	3d 00 00             	cmp    $0x0,%ax
    1472:	7c 03                	jl     0x1477
    1474:	e9 06 00             	jmp    0x147d
    1477:	b8 00 00             	mov    $0x0,%ax
    147a:	e9 be 03             	jmp    0x183b
    147d:	ff 76 0e             	push   0xe(%bp)
    1480:	b8 8b 00             	mov    $0x8b,%ax
    1483:	1e                   	push   %ds
    1484:	50                   	push   %ax
    1485:	8b 5e cc             	mov    -0x34(%bp),%bx
    1488:	8b c3                	mov    %bx,%ax
    148a:	d1 e3                	shl    $1,%bx
    148c:	d1 e3                	shl    $1,%bx
    148e:	03 d8                	add    %ax,%bx
    1490:	d1 e3                	shl    $1,%bx
    1492:	8b 87 28 02          	mov    0x228(%bx),%ax
    1496:	89 46 ca             	mov    %ax,-0x36(%bp)
    1499:	50                   	push   %ax
    149a:	9a ff ff 00 00       	lcall  $0x0,$0xffff
    149f:	3d 00 00             	cmp    $0x0,%ax
    14a2:	74 03                	je     0x14a7
    14a4:	e9 12 00             	jmp    0x14b9
    14a7:	ff 76 0e             	push   0xe(%bp)
    14aa:	b8 ff ff             	mov    $0xffff,%ax
    14ad:	50                   	push   %ax
    14ae:	9a 1b 15 00 00       	lcall  $0x0,$0x151b
    14b3:	b8 01 00             	mov    $0x1,%ax
    14b6:	e9 82 03             	jmp    0x183b
    14b9:	e9 10 00             	jmp    0x14cc
    14bc:	ff 76 0e             	push   0xe(%bp)
    14bf:	b8 93 00             	mov    $0x93,%ax
    14c2:	1e                   	push   %ds
    14c3:	50                   	push   %ax
    14c4:	9a ff ff 00 00       	lcall  $0x0,$0xffff
    14c9:	89 46 ca             	mov    %ax,-0x36(%bp)
    14cc:	83 7e ca 00          	cmpw   $0x0,-0x36(%bp)
    14d0:	74 03                	je     0x14d5
    14d2:	e9 06 00             	jmp    0x14db
    14d5:	b8 00 00             	mov    $0x0,%ax
    14d8:	e9 60 03             	jmp    0x183b
    14db:	ff 76 ca             	push   -0x36(%bp)
    14de:	9a ff ff 00 00       	lcall  $0x0,$0xffff
    14e3:	89 46 d8             	mov    %ax,-0x28(%bp)
    14e6:	89 56 da             	mov    %dx,-0x26(%bp)
    14e9:	0b d0                	or     %ax,%dx
    14eb:	74 03                	je     0x14f0
    14ed:	e9 06 00             	jmp    0x14f6
    14f0:	b8 00 00             	mov    $0x0,%ax
    14f3:	e9 45 03             	jmp    0x183b
    14f6:	81 7e 0c 10 01       	cmpw   $0x110,0xc(%bp)
    14fb:	74 03                	je     0x1500
    14fd:	e9 b2 02             	jmp    0x17b2
    1500:	ff 76 0e             	push   0xe(%bp)
    1503:	9a 26 0f 00 00       	lcall  $0x0,$0xf26
    1508:	89 46 ce             	mov    %ax,-0x32(%bp)
    150b:	3d 00 00             	cmp    $0x0,%ax
    150e:	74 03                	je     0x1513
    1510:	e9 1a 00             	jmp    0x152d
    1513:	ff 76 0e             	push   0xe(%bp)
    1516:	b8 ff ff             	mov    $0xffff,%ax
    1519:	50                   	push   %ax
    151a:	9a 55 15 00 00       	lcall  $0x0,$0x1555
    151f:	ff 76 ca             	push   -0x36(%bp)
    1522:	9a 5d 15 00 00       	lcall  $0x0,$0x155d
    1527:	b8 01 00             	mov    $0x1,%ax
    152a:	e9 0e 03             	jmp    0x183b
    152d:	ff 76 ce             	push   -0x32(%bp)
    1530:	8d 46 dc             	lea    -0x24(%bp),%ax
    1533:	16                   	push   %ss
    1534:	50                   	push   %ax
    1535:	9a 44 0f 00 00       	lcall  $0x0,$0xf44
    153a:	3d 00 00             	cmp    $0x0,%ax
    153d:	74 03                	je     0x1542
    153f:	e9 25 00             	jmp    0x1567
    1542:	ff 76 0e             	push   0xe(%bp)
    1545:	ff 76 ce             	push   -0x32(%bp)
    1548:	9a 6e 15 00 00       	lcall  $0x0,$0x156e
    154d:	ff 76 0e             	push   0xe(%bp)
    1550:	b8 ff ff             	mov    $0xffff,%ax
    1553:	50                   	push   %ax
    1554:	9a 56 16 00 00       	lcall  $0x0,$0x1656
    1559:	ff 76 ca             	push   -0x36(%bp)
    155c:	9a 5e 16 00 00       	lcall  $0x0,$0x165e
    1561:	b8 01 00             	mov    $0x1,%ax
    1564:	e9 d4 02             	jmp    0x183b
    1567:	ff 76 0e             	push   0xe(%bp)
    156a:	ff 76 ce             	push   -0x32(%bp)
    156d:	9a 57 0f 00 00       	lcall  $0x0,$0xf57
    1572:	8b 46 dc             	mov    -0x24(%bp),%ax
    1575:	89 46 c4             	mov    %ax,-0x3c(%bp)
    1578:	b8 00 00             	mov    $0x0,%ax
    157b:	50                   	push   %ax
    157c:	9a 96 15 00 00       	lcall  $0x0,$0x1596
    1581:	89 46 fc             	mov    %ax,-0x4(%bp)
    1584:	3d f0 00             	cmp    $0xf0,%ax
    1587:	7f 03                	jg     0x158c
    1589:	e9 05 00             	jmp    0x1591
    158c:	c7 46 fc f0 00       	movw   $0xf0,-0x4(%bp)
    1591:	b8 04 00             	mov    $0x4,%ax
    1594:	50                   	push   %ax
    1595:	9a a1 15 00 00       	lcall  $0x0,$0x15a1
    159a:	b9 08 00             	mov    $0x8,%cx
    159d:	51                   	push   %cx
    159e:	8b f0                	mov    %ax,%si
    15a0:	9a be 15 00 00       	lcall  $0x0,$0x15be
    15a5:	8b 4e c4             	mov    -0x3c(%bp),%cx
    15a8:	d1 e1                	shl    $1,%cx
    15aa:	03 c1                	add    %cx,%ax
    15ac:	05 07 00             	add    $0x7,%ax
    15af:	d1 e0                	shl    $1,%ax
    15b1:	03 f0                	add    %ax,%si
    15b3:	89 76 c6             	mov    %si,-0x3a(%bp)
    15b6:	ff 76 0e             	push   0xe(%bp)
    15b9:	b8 00 00             	mov    $0x0,%ax
    15bc:	50                   	push   %ax
    15bd:	9a d0 15 00 00       	lcall  $0x0,$0x15d0
    15c2:	2b 46 fc             	sub    -0x4(%bp),%ax
    15c5:	99                   	cwtd
    15c6:	2b c2                	sub    %dx,%ax
    15c8:	d1 f8                	sar    $1,%ax
    15ca:	50                   	push   %ax
    15cb:	b8 01 00             	mov    $0x1,%ax
    15ce:	50                   	push   %ax
    15cf:	9a 8e 0f 00 00       	lcall  $0x0,$0xf8e
    15d4:	2b 46 c6             	sub    -0x3a(%bp),%ax
    15d7:	99                   	cwtd
    15d8:	2b c2                	sub    %dx,%ax
    15da:	d1 f8                	sar    $1,%ax
    15dc:	50                   	push   %ax
    15dd:	ff 76 fc             	push   -0x4(%bp)
    15e0:	ff 76 c6             	push   -0x3a(%bp)
    15e3:	b8 00 00             	mov    $0x0,%ax
    15e6:	50                   	push   %ax
    15e7:	9a ce 0f 00 00       	lcall  $0x0,$0xfce
    15ec:	ff 76 0e             	push   0xe(%bp)
    15ef:	8b 46 d8             	mov    -0x28(%bp),%ax
    15f2:	8b 56 da             	mov    -0x26(%bp),%dx
    15f5:	05 42 00             	add    $0x42,%ax
    15f8:	52                   	push   %dx
    15f9:	50                   	push   %ax
    15fa:	9a ff ff 00 00       	lcall  $0x0,$0xffff
    15ff:	ff 76 0e             	push   0xe(%bp)
    1602:	8d 46 d0             	lea    -0x30(%bp),%ax
    1605:	16                   	push   %ss
    1606:	50                   	push   %ax
    1607:	9a db 0f 00 00       	lcall  $0x0,$0xfdb
    160c:	8b 46 d4             	mov    -0x2c(%bp),%ax
    160f:	89 46 fc             	mov    %ax,-0x4(%bp)
    1612:	b8 6e 00             	mov    $0x6e,%ax
    1615:	50                   	push   %ax
    1616:	8b 46 c4             	mov    -0x3c(%bp),%ax
    1619:	40                   	inc    %ax
    161a:	d1 e0                	shl    $1,%ax
    161c:	50                   	push   %ax
    161d:	8b 46 fc             	mov    -0x4(%bp),%ax
    1620:	2d 08 00             	sub    $0x8,%ax
    1623:	50                   	push   %ax
    1624:	b8 04 00             	mov    $0x4,%ax
    1627:	50                   	push   %ax
    1628:	50                   	push   %ax
    1629:	2b c0                	sub    %ax,%ax
    162b:	50                   	push   %ax
    162c:	50                   	push   %ax
    162d:	8b 46 d8             	mov    -0x28(%bp),%ax
    1630:	8b 56 da             	mov    -0x26(%bp),%dx
    1633:	05 02 00             	add    $0x2,%ax
    1636:	52                   	push   %dx
    1637:	50                   	push   %ax
    1638:	b8 9b 00             	mov    $0x9b,%ax
    163b:	1e                   	push   %ds
    163c:	50                   	push   %ax
    163d:	ff 76 0e             	push   0xe(%bp)
    1640:	e8 4c f8             	call   0xe8f
    1643:	83 c4 18             	add    $0x18,%sp
    1646:	3d 00 00             	cmp    $0x0,%ax
    1649:	74 03                	je     0x164e
    164b:	e9 1a 00             	jmp    0x1668
    164e:	ff 76 0e             	push   0xe(%bp)
    1651:	b8 ff ff             	mov    $0xffff,%ax
    1654:	50                   	push   %ax
    1655:	9a ff ff 00 00       	lcall  $0x0,$0xffff
    165a:	ff 76 ca             	push   -0x36(%bp)
    165d:	9a ff ff 00 00       	lcall  $0x0,$0xffff
    1662:	b8 01 00             	mov    $0x1,%ax
    1665:	e9 d3 01             	jmp    0x183b
    1668:	8b 46 fc             	mov    -0x4(%bp),%ax
    166b:	2d 0c 00             	sub    $0xc,%ax
    166e:	99                   	cwtd
    166f:	2b c2                	sub    %dx,%ax
    1671:	d1 f8                	sar    $1,%ax
    1673:	89 46 c8             	mov    %ax,-0x38(%bp)
    1676:	c4 5e d8             	les    -0x28(%bp),%bx
    1679:	26 83 3f 00          	cmpw   $0x0,%es:(%bx)
    167d:	75 03                	jne    0x1682
    167f:	e9 af 00             	jmp    0x1731
    1682:	b8 06 00             	mov    $0x6,%ax
    1685:	50                   	push   %ax
    1686:	8b 46 c4             	mov    -0x3c(%bp),%ax
    1689:	05 04 00             	add    $0x4,%ax
    168c:	50                   	push   %ax
    168d:	ff 76 c8             	push   -0x38(%bp)
    1690:	8b 46 d6             	mov    -0x2a(%bp),%ax
    1693:	2b 46 c4             	sub    -0x3c(%bp),%ax
    1696:	2d 07 00             	sub    $0x7,%ax
    1699:	50                   	push   %ax
    169a:	b8 04 00             	mov    $0x4,%ax
    169d:	50                   	push   %ax
    169e:	b9 00 00             	mov    $0x0,%cx
    16a1:	ba 01 00             	mov    $0x1,%dx
    16a4:	52                   	push   %dx
    16a5:	51                   	push   %cx
    16a6:	b9 a2 00             	mov    $0xa2,%cx
    16a9:	1e                   	push   %ds
    16aa:	51                   	push   %cx
    16ab:	b9 a7 00             	mov    $0xa7,%cx
    16ae:	1e                   	push   %ds
    16af:	51                   	push   %cx
    16b0:	ff 76 0e             	push   0xe(%bp)
    16b3:	e8 d9 f7             	call   0xe8f
    16b6:	83 c4 18             	add    $0x18,%sp
    16b9:	3d 00 00             	cmp    $0x0,%ax
    16bc:	75 03                	jne    0x16c1
    16be:	e9 41 00             	jmp    0x1702
    16c1:	b8 07 00             	mov    $0x7,%ax
    16c4:	50                   	push   %ax
    16c5:	8b 4e c4             	mov    -0x3c(%bp),%cx
    16c8:	83 c1 04             	add    $0x4,%cx
    16cb:	51                   	push   %cx
    16cc:	ff 76 c8             	push   -0x38(%bp)
    16cf:	8b 4e d6             	mov    -0x2a(%bp),%cx
    16d2:	2b 4e c4             	sub    -0x3c(%bp),%cx
    16d5:	2b c8                	sub    %ax,%cx
    16d7:	51                   	push   %cx
    16d8:	8b 46 c8             	mov    -0x38(%bp),%ax
    16db:	05 08 00             	add    $0x8,%ax
    16de:	50                   	push   %ax
    16df:	b8 01 00             	mov    $0x1,%ax
    16e2:	ba 01 00             	mov    $0x1,%dx
    16e5:	52                   	push   %dx
    16e6:	50                   	push   %ax
    16e7:	b8 ae 00             	mov    $0xae,%ax
    16ea:	1e                   	push   %ds
    16eb:	50                   	push   %ax
    16ec:	b8 b2 00             	mov    $0xb2,%ax
    16ef:	1e                   	push   %ds
    16f0:	50                   	push   %ax
    16f1:	ff 76 0e             	push   0xe(%bp)
    16f4:	e8 98 f7             	call   0xe8f
    16f7:	83 c4 18             	add    $0x18,%sp
    16fa:	3d 00 00             	cmp    $0x0,%ax
    16fd:	74 03                	je     0x1702
    16ff:	e9 1a 00             	jmp    0x171c
    1702:	ff 76 0e             	push   0xe(%bp)
    1705:	b8 ff ff             	mov    $0xffff,%ax
    1708:	50                   	push   %ax
    1709:	9a 80 17 00 00       	lcall  $0x0,$0x1780
    170e:	ff 76 ca             	push   -0x36(%bp)
    1711:	9a 88 17 00 00       	lcall  $0x0,$0x1788
    1716:	b8 01 00             	mov    $0x1,%ax
    1719:	e9 1f 01             	jmp    0x183b
    171c:	ff 76 0e             	push   0xe(%bp)
    171f:	b8 07 00             	mov    $0x7,%ax
    1722:	50                   	push   %ax
    1723:	9a 9a 17 00 00       	lcall  $0x0,$0x179a
    1728:	50                   	push   %ax
    1729:	9a a0 17 00 00       	lcall  $0x0,$0x17a0
    172e:	e9 73 00             	jmp    0x17a4
    1731:	b8 01 00             	mov    $0x1,%ax
    1734:	50                   	push   %ax
    1735:	8b 4e c4             	mov    -0x3c(%bp),%cx
    1738:	83 c1 04             	add    $0x4,%cx
    173b:	51                   	push   %cx
    173c:	ff 76 c8             	push   -0x38(%bp)
    173f:	8b 4e d6             	mov    -0x2a(%bp),%cx
    1742:	2b 4e c4             	sub    -0x3c(%bp),%cx
    1745:	83 e9 07             	sub    $0x7,%cx
    1748:	51                   	push   %cx
    1749:	8b 46 fc             	mov    -0x4(%bp),%ax
    174c:	2b 46 c8             	sub    -0x38(%bp),%ax
    174f:	99                   	cwtd
    1750:	2b c2                	sub    %dx,%ax
    1752:	d1 f8                	sar    $1,%ax
    1754:	50                   	push   %ax
    1755:	b8 01 00             	mov    $0x1,%ax
    1758:	ba 01 00             	mov    $0x1,%dx
    175b:	52                   	push   %dx
    175c:	50                   	push   %ax
    175d:	b8 b9 00             	mov    $0xb9,%ax
    1760:	1e                   	push   %ds
    1761:	50                   	push   %ax
    1762:	b8 bc 00             	mov    $0xbc,%ax
    1765:	1e                   	push   %ds
    1766:	50                   	push   %ax
    1767:	ff 76 0e             	push   0xe(%bp)
    176a:	e8 22 f7             	call   0xe8f
    176d:	83 c4 18             	add    $0x18,%sp
    1770:	3d 00 00             	cmp    $0x0,%ax
    1773:	74 03                	je     0x1778
    1775:	e9 1a 00             	jmp    0x1792
    1778:	ff 76 0e             	push   0xe(%bp)
    177b:	b8 ff ff             	mov    $0xffff,%ax
    177e:	50                   	push   %ax
    177f:	9a e7 17 00 00       	lcall  $0x0,$0x17e7
    1784:	ff 76 ca             	push   -0x36(%bp)
    1787:	9a a8 17 00 00       	lcall  $0x0,$0x17a8
    178c:	b8 01 00             	mov    $0x1,%ax
    178f:	e9 a9 00             	jmp    0x183b
    1792:	ff 76 0e             	push   0xe(%bp)
    1795:	b8 01 00             	mov    $0x1,%ax
    1798:	50                   	push   %ax
    1799:	9a ff ff 00 00       	lcall  $0x0,$0xffff
    179e:	50                   	push   %ax
    179f:	9a ff ff 00 00       	lcall  $0x0,$0xffff
    17a4:	ff 76 ca             	push   -0x36(%bp)
    17a7:	9a 23 18 00 00       	lcall  $0x0,$0x1823
    17ac:	b8 00 00             	mov    $0x0,%ax
    17af:	e9 89 00             	jmp    0x183b
    17b2:	81 7e 0c 11 01       	cmpw   $0x111,0xc(%bp)
    17b7:	74 03                	je     0x17bc
    17b9:	e9 32 00             	jmp    0x17ee
    17bc:	83 7e 0a 06          	cmpw   $0x6,0xa(%bp)
    17c0:	75 03                	jne    0x17c5
    17c2:	e9 1b 00             	jmp    0x17e0
    17c5:	83 7e 0a 07          	cmpw   $0x7,0xa(%bp)
    17c9:	75 03                	jne    0x17ce
    17cb:	e9 12 00             	jmp    0x17e0
    17ce:	83 7e 0a 01          	cmpw   $0x1,0xa(%bp)
    17d2:	75 03                	jne    0x17d7
    17d4:	e9 09 00             	jmp    0x17e0
    17d7:	83 7e 0a 02          	cmpw   $0x2,0xa(%bp)
    17db:	74 03                	je     0x17e0
    17dd:	e9 0b 00             	jmp    0x17eb
    17e0:	ff 76 0e             	push   0xe(%bp)
    17e3:	ff 76 0a             	push   0xa(%bp)
    17e6:	9a ff 17 00 00       	lcall  $0x0,$0x17ff
    17eb:	e9 3f 00             	jmp    0x182d
    17ee:	83 7e 0c 10          	cmpw   $0x10,0xc(%bp)
    17f2:	74 03                	je     0x17f7
    17f4:	e9 0f 00             	jmp    0x1806
    17f7:	ff 76 0e             	push   0xe(%bp)
    17fa:	b8 02 00             	mov    $0x2,%ax
    17fd:	50                   	push   %ax
    17fe:	9a 7d 18 00 00       	lcall  $0x0,$0x187d
    1803:	e9 27 00             	jmp    0x182d
    1806:	83 7e 0c 02          	cmpw   $0x2,0xc(%bp)
    180a:	74 03                	je     0x180f
    180c:	e9 10 00             	jmp    0x181f
    180f:	ff 76 0e             	push   0xe(%bp)
    1812:	b8 c3 00             	mov    $0xc3,%ax
    1815:	1e                   	push   %ds
    1816:	50                   	push   %ax
    1817:	9a ff ff 00 00       	lcall  $0x0,$0xffff
    181c:	e9 0e 00             	jmp    0x182d
    181f:	ff 76 ca             	push   -0x36(%bp)
    1822:	9a 31 18 00 00       	lcall  $0x0,$0x1831
    1827:	b8 00 00             	mov    $0x0,%ax
    182a:	e9 0e 00             	jmp    0x183b
    182d:	ff 76 ca             	push   -0x36(%bp)
    1830:	9a ea 19 00 00       	lcall  $0x0,$0x19ea
    1835:	b8 01 00             	mov    $0x1,%ax
    1838:	e9 00 00             	jmp    0x183b
    183b:	5e                   	pop    %si
    183c:	5f                   	pop    %di
    183d:	83 ed 02             	sub    $0x2,%bp
    1840:	8b e5                	mov    %bp,%sp
    1842:	1f                   	pop    %ds
    1843:	5d                   	pop    %bp
    1844:	4d                   	dec    %bp
    1845:	ca 0a 00             	lret   $0xa
    1848:	55                   	push   %bp
    1849:	8b ec                	mov    %sp,%bp
    184b:	81 ec 00 00          	sub    $0x0,%sp
    184f:	57                   	push   %di
    1850:	56                   	push   %si
    1851:	83 7e 06 00          	cmpw   $0x0,0x6(%bp)
    1855:	7d 03                	jge    0x185a
    1857:	e9 1b 00             	jmp    0x1875
    185a:	8b 46 08             	mov    0x8(%bp),%ax
    185d:	8b 56 0a             	mov    0xa(%bp),%dx
    1860:	8b 5e 06             	mov    0x6(%bp),%bx
    1863:	8b cb                	mov    %bx,%cx
    1865:	d1 e3                	shl    $1,%bx
    1867:	d1 e3                	shl    $1,%bx
    1869:	03 d9                	add    %cx,%bx
    186b:	d1 e3                	shl    $1,%bx
    186d:	89 87 22 02          	mov    %ax,0x222(%bx)
    1871:	89 97 24 02          	mov    %dx,0x224(%bx)
    1875:	ff 76 04             	push   0x4(%bp)
    1878:	b8 00 00             	mov    $0x0,%ax
    187b:	50                   	push   %ax
    187c:	9a af 14 00 00       	lcall  $0x0,$0x14af
    1881:	b8 02 00             	mov    $0x2,%ax
    1884:	e9 00 00             	jmp    0x1887
    1887:	5e                   	pop    %si
    1888:	5f                   	pop    %di
    1889:	8b e5                	mov    %bp,%sp
    188b:	5d                   	pop    %bp
    188c:	c3                   	ret
    188d:	55                   	push   %bp
    188e:	8b ec                	mov    %sp,%bp
    1890:	81 ec 16 00          	sub    $0x16,%sp
    1894:	57                   	push   %di
    1895:	56                   	push   %si
    1896:	e8 15 e8             	call   0xae
    1899:	89 46 f0             	mov    %ax,-0x10(%bp)
    189c:	c7 46 ea 02 00       	movw   $0x2,-0x16(%bp)
    18a1:	83 7e f0 00          	cmpw   $0x0,-0x10(%bp)
    18a5:	7d 03                	jge    0x18aa
    18a7:	e9 17 00             	jmp    0x18c1
    18aa:	8b 5e f0             	mov    -0x10(%bp),%bx
    18ad:	8b c3                	mov    %bx,%ax
    18af:	d1 e3                	shl    $1,%bx
    18b1:	d1 e3                	shl    $1,%bx
    18b3:	03 d8                	add    %ax,%bx
    18b5:	d1 e3                	shl    $1,%bx
    18b7:	83 bf 28 02 00       	cmpw   $0x0,0x228(%bx)
    18bc:	75 03                	jne    0x18c1
    18be:	e9 17 00             	jmp    0x18d8
    18c1:	b8 02 00             	mov    $0x2,%ax
    18c4:	ba 00 00             	mov    $0x0,%dx
    18c7:	52                   	push   %dx
    18c8:	50                   	push   %ax
    18c9:	ff 76 f0             	push   -0x10(%bp)
    18cc:	ff 76 04             	push   0x4(%bp)
    18cf:	e8 76 ff             	call   0x1848
    18d2:	83 c4 08             	add    $0x8,%sp
    18d5:	e9 51 02             	jmp    0x1b29
    18d8:	b8 40 00             	mov    $0x40,%ax
    18db:	50                   	push   %ax
    18dc:	b8 82 00             	mov    $0x82,%ax
    18df:	ba 00 00             	mov    $0x0,%dx
    18e2:	52                   	push   %dx
    18e3:	50                   	push   %ax
    18e4:	9a d7 19 00 00       	lcall  $0x0,$0x19d7
    18e9:	89 46 ee             	mov    %ax,-0x12(%bp)
    18ec:	3d 00 00             	cmp    $0x0,%ax
    18ef:	74 03                	je     0x18f4
    18f1:	e9 17 00             	jmp    0x190b
    18f4:	b8 09 00             	mov    $0x9,%ax
    18f7:	ba 00 00             	mov    $0x0,%dx
    18fa:	52                   	push   %dx
    18fb:	50                   	push   %ax
    18fc:	ff 76 f0             	push   -0x10(%bp)
    18ff:	ff 76 04             	push   0x4(%bp)
    1902:	e8 43 ff             	call   0x1848
    1905:	83 c4 08             	add    $0x8,%sp
    1908:	e9 1e 02             	jmp    0x1b29
    190b:	ff 76 ee             	push   -0x12(%bp)
    190e:	9a 11 1a 00 00       	lcall  $0x0,$0x1a11
    1913:	89 46 fc             	mov    %ax,-0x4(%bp)
    1916:	89 56 fe             	mov    %dx,-0x2(%bp)
    1919:	0b d0                	or     %ax,%dx
    191b:	74 03                	je     0x1920
    191d:	e9 1f 00             	jmp    0x193f
    1920:	ff 76 ee             	push   -0x12(%bp)
    1923:	9a f2 19 00 00       	lcall  $0x0,$0x19f2
    1928:	b8 0a 00             	mov    $0xa,%ax
    192b:	ba 00 00             	mov    $0x0,%dx
    192e:	52                   	push   %dx
    192f:	50                   	push   %ax
    1930:	ff 76 f0             	push   -0x10(%bp)
    1933:	ff 76 04             	push   0x4(%bp)
    1936:	e8 0f ff             	call   0x1848
    1939:	83 c4 08             	add    $0x8,%sp
    193c:	e9 ea 01             	jmp    0x1b29
    193f:	8b 46 0e             	mov    0xe(%bp),%ax
    1942:	c4 5e fc             	les    -0x4(%bp),%bx
    1945:	26 89 07             	mov    %ax,%es:(%bx)
    1948:	b8 40 00             	mov    $0x40,%ax
    194b:	50                   	push   %ax
    194c:	ff 76 08             	push   0x8(%bp)
    194f:	ff 76 06             	push   0x6(%bp)
    1952:	8b 4e fc             	mov    -0x4(%bp),%cx
    1955:	8b 56 fe             	mov    -0x2(%bp),%dx
    1958:	83 c1 02             	add    $0x2,%cx
    195b:	52                   	push   %dx
    195c:	51                   	push   %cx
    195d:	e8 cc e8             	call   0x22c
    1960:	83 c4 0a             	add    $0xa,%sp
    1963:	b8 40 00             	mov    $0x40,%ax
    1966:	50                   	push   %ax
    1967:	8b 46 fc             	mov    -0x4(%bp),%ax
    196a:	8b 56 fe             	mov    -0x2(%bp),%dx
    196d:	05 42 00             	add    $0x42,%ax
    1970:	52                   	push   %dx
    1971:	50                   	push   %ax
    1972:	ff 76 0c             	push   0xc(%bp)
    1975:	ff 76 0a             	push   0xa(%bp)
    1978:	e8 e2 ed             	call   0x75d
    197b:	83 c4 0a             	add    $0xa,%sp
    197e:	3d 00 00             	cmp    $0x0,%ax
    1981:	75 03                	jne    0x1986
    1983:	e9 44 00             	jmp    0x19ca
    1986:	c7 46 ec 00 00       	movw   $0x0,-0x14(%bp)
    198b:	e9 03 00             	jmp    0x1991
    198e:	ff 46 ec             	incw   -0x14(%bp)
    1991:	83 7e ec 3f          	cmpw   $0x3f,-0x14(%bp)
    1995:	72 03                	jb     0x199a
    1997:	e9 25 00             	jmp    0x19bf
    199a:	c4 5e 0a             	les    0xa(%bp),%bx
    199d:	8b 76 ec             	mov    -0x14(%bp),%si
    19a0:	26 80 38 00          	cmpb   $0x0,%es:(%bx,%si)
    19a4:	75 03                	jne    0x19a9
    19a6:	e9 16 00             	jmp    0x19bf
    19a9:	c4 5e 0a             	les    0xa(%bp),%bx
    19ac:	8b 76 ec             	mov    -0x14(%bp),%si
    19af:	26 8a 00             	mov    %es:(%bx,%si),%al
    19b2:	c4 5e fc             	les    -0x4(%bp),%bx
    19b5:	8b 76 ec             	mov    -0x14(%bp),%si
    19b8:	26 88 40 42          	mov    %al,%es:0x42(%bx,%si)
    19bc:	e9 cf ff             	jmp    0x198e
    19bf:	c4 5e fc             	les    -0x4(%bp),%bx
    19c2:	8b 76 ec             	mov    -0x14(%bp),%si
    19c5:	26 c6 40 42 00       	movb   $0x0,%es:0x42(%bx,%si)
    19ca:	b8 42 00             	mov    $0x42,%ax
    19cd:	50                   	push   %ax
    19ce:	b8 20 00             	mov    $0x20,%ax
    19d1:	ba 00 00             	mov    $0x0,%dx
    19d4:	52                   	push   %dx
    19d5:	50                   	push   %ax
    19d6:	9a ff ff 00 00       	lcall  $0x0,$0xffff
    19db:	89 46 f2             	mov    %ax,-0xe(%bp)
    19de:	3d 00 00             	cmp    $0x0,%ax
    19e1:	74 03                	je     0x19e6
    19e3:	e9 27 00             	jmp    0x1a0d
    19e6:	ff 76 ee             	push   -0x12(%bp)
    19e9:	9a 2e 1a 00 00       	lcall  $0x0,$0x1a2e
    19ee:	ff 76 ee             	push   -0x12(%bp)
    19f1:	9a 26 1a 00 00       	lcall  $0x0,$0x1a26
    19f6:	b8 09 00             	mov    $0x9,%ax
    19f9:	ba 00 00             	mov    $0x0,%dx
    19fc:	52                   	push   %dx
    19fd:	50                   	push   %ax
    19fe:	ff 76 f0             	push   -0x10(%bp)
    1a01:	ff 76 04             	push   0x4(%bp)
    1a04:	e8 41 fe             	call   0x1848
    1a07:	83 c4 08             	add    $0x8,%sp
    1a0a:	e9 1c 01             	jmp    0x1b29
    1a0d:	ff 76 f2             	push   -0xe(%bp)
    1a10:	9a df 14 00 00       	lcall  $0x0,$0x14df
    1a15:	89 46 f8             	mov    %ax,-0x8(%bp)
    1a18:	89 56 fa             	mov    %dx,-0x6(%bp)
    1a1b:	0b d0                	or     %ax,%dx
    1a1d:	74 03                	je     0x1a22
    1a1f:	e9 2f 00             	jmp    0x1a51
    1a22:	ff 76 f2             	push   -0xe(%bp)
    1a25:	9a 36 1a 00 00       	lcall  $0x0,$0x1a36
    1a2a:	ff 76 ee             	push   -0x12(%bp)
    1a2d:	9a 73 1a 00 00       	lcall  $0x0,$0x1a73
    1a32:	ff 76 ee             	push   -0x12(%bp)
    1a35:	9a ff ff 00 00       	lcall  $0x0,$0xffff
    1a3a:	b8 0a 00             	mov    $0xa,%ax
    1a3d:	ba 00 00             	mov    $0x0,%dx
    1a40:	52                   	push   %dx
    1a41:	50                   	push   %ax
    1a42:	ff 76 f0             	push   -0x10(%bp)
    1a45:	ff 76 04             	push   0x4(%bp)
    1a48:	e8 fd fd             	call   0x1848
    1a4b:	83 c4 08             	add    $0x8,%sp
    1a4e:	e9 d8 00             	jmp    0x1b29
    1a51:	c4 5e f8             	les    -0x8(%bp),%bx
    1a54:	26 c7 07 80 00       	movw   $0x80,%es:(%bx)
    1a59:	26 c7 47 02 c8 80    	movw   $0x80c8,%es:0x2(%bx)
    1a5f:	c4 5e f8             	les    -0x8(%bp),%bx
    1a62:	26 c6 47 09 46       	movb   $0x46,%es:0x9(%bx)
    1a67:	c4 5e f8             	les    -0x8(%bp),%bx
    1a6a:	26 c6 47 0b 28       	movb   $0x28,%es:0xb(%bx)
    1a6f:	ff 76 f2             	push   -0xe(%bp)
    1a72:	9a 23 15 00 00       	lcall  $0x0,$0x1523
    1a77:	8b 46 ee             	mov    -0x12(%bp),%ax
    1a7a:	8b 5e f0             	mov    -0x10(%bp),%bx
    1a7d:	8b cb                	mov    %bx,%cx
    1a7f:	d1 e3                	shl    $1,%bx
    1a81:	d1 e3                	shl    $1,%bx
    1a83:	03 d9                	add    %cx,%bx
    1a85:	d1 e3                	shl    $1,%bx
    1a87:	89 87 28 02          	mov    %ax,0x228(%bx)
    1a8b:	b8 ff ff             	mov    $0xffff,%ax
    1a8e:	ba 00 00             	mov    $0x0,%dx
    1a91:	52                   	push   %dx
    1a92:	50                   	push   %ax
    1a93:	ff 36 1e 02          	push   0x21e
    1a97:	9a ff ff 00 00       	lcall  $0x0,$0xffff
    1a9c:	89 46 f4             	mov    %ax,-0xc(%bp)
    1a9f:	89 56 f6             	mov    %dx,-0xa(%bp)
    1aa2:	8b 46 f6             	mov    -0xa(%bp),%ax
    1aa5:	0b 46 f4             	or     -0xc(%bp),%ax
    1aa8:	75 03                	jne    0x1aad
    1aaa:	e9 26 00             	jmp    0x1ad3
    1aad:	ff 36 1e 02          	push   0x21e
    1ab1:	ff 76 f2             	push   -0xe(%bp)
    1ab4:	ff 76 04             	push   0x4(%bp)
    1ab7:	ff 76 f6             	push   -0xa(%bp)
    1aba:	ff 76 f4             	push   -0xc(%bp)
    1abd:	9a ff ff 00 00       	lcall  $0x0,$0xffff
    1ac2:	89 46 ea             	mov    %ax,-0x16(%bp)
    1ac5:	ff 76 f6             	push   -0xa(%bp)
    1ac8:	ff 76 f4             	push   -0xc(%bp)
    1acb:	9a ff ff 00 00       	lcall  $0x0,$0xffff
    1ad0:	e9 05 00             	jmp    0x1ad8
    1ad3:	c7 46 ea ff ff       	movw   $0xffff,-0x16(%bp)
    1ad8:	8b 5e f0             	mov    -0x10(%bp),%bx
    1adb:	8b c3                	mov    %bx,%ax
    1add:	d1 e3                	shl    $1,%bx
    1adf:	d1 e3                	shl    $1,%bx
    1ae1:	03 d8                	add    %ax,%bx
    1ae3:	d1 e3                	shl    $1,%bx
    1ae5:	c7 87 28 02 00 00    	movw   $0x0,0x228(%bx)
    1aeb:	ff 76 f2             	push   -0xe(%bp)
    1aee:	9a ff 1a 00 00       	lcall  $0x0,$0x1aff
    1af3:	ff 76 ee             	push   -0x12(%bp)
    1af6:	9a 12 17 00 00       	lcall  $0x0,$0x1712
    1afb:	ff 76 ee             	push   -0x12(%bp)
    1afe:	9a 24 19 00 00       	lcall  $0x0,$0x1924
    1b03:	83 7e ea 00          	cmpw   $0x0,-0x16(%bp)
    1b07:	7c 03                	jl     0x1b0c
    1b09:	e9 17 00             	jmp    0x1b23
    1b0c:	b8 02 00             	mov    $0x2,%ax
    1b0f:	ba 00 00             	mov    $0x0,%dx
    1b12:	52                   	push   %dx
    1b13:	50                   	push   %ax
    1b14:	ff 76 f0             	push   -0x10(%bp)
    1b17:	ff 76 04             	push   0x4(%bp)
    1b1a:	e8 2b fd             	call   0x1848
    1b1d:	83 c4 08             	add    $0x8,%sp
    1b20:	e9 06 00             	jmp    0x1b29
    1b23:	8b 46 ea             	mov    -0x16(%bp),%ax
    1b26:	e9 00 00             	jmp    0x1b29
    1b29:	5e                   	pop    %si
    1b2a:	5f                   	pop    %di
    1b2b:	8b e5                	mov    %bp,%sp
    1b2d:	5d                   	pop    %bp
    1b2e:	c3                   	ret
    1b2f:	55                   	push   %bp
    1b30:	8b ec                	mov    %sp,%bp
    1b32:	81 ec 00 00          	sub    $0x0,%sp
    1b36:	57                   	push   %di
    1b37:	56                   	push   %si
    1b38:	b8 00 00             	mov    $0x0,%ax
    1b3b:	50                   	push   %ax
    1b3c:	b8 cb 00             	mov    $0xcb,%ax
    1b3f:	1e                   	push   %ds
    1b40:	50                   	push   %ax
    1b41:	ff 76 08             	push   0x8(%bp)
    1b44:	ff 76 06             	push   0x6(%bp)
    1b47:	ff 76 04             	push   0x4(%bp)
    1b4a:	e8 40 fd             	call   0x188d
    1b4d:	83 c4 0c             	add    $0xc,%sp
    1b50:	5e                   	pop    %si
    1b51:	5f                   	pop    %di
    1b52:	8b e5                	mov    %bp,%sp
    1b54:	5d                   	pop    %bp
    1b55:	c3                   	ret
    1b56:	55                   	push   %bp
    1b57:	8b ec                	mov    %sp,%bp
    1b59:	81 ec 00 00          	sub    $0x0,%sp
    1b5d:	57                   	push   %di
    1b5e:	56                   	push   %si
    1b5f:	c4 5e 04             	les    0x4(%bp),%bx
    1b62:	26 83 bf 9e 10 ff    	cmpw   $0xffff,%es:0x109e(%bx)
    1b68:	75 03                	jne    0x1b6d
    1b6a:	e9 23 00             	jmp    0x1b90
    1b6d:	c4 5e 04             	les    0x4(%bp),%bx
    1b70:	26 ff b7 9e 10       	push   %es:0x109e(%bx)
    1b75:	9a ff ff 00 00       	lcall  $0x0,$0xffff
    1b7a:	40                   	inc    %ax
    1b7b:	74 03                	je     0x1b80
    1b7d:	e9 06 00             	jmp    0x1b86
    1b80:	b8 00 00             	mov    $0x0,%ax
    1b83:	e9 52 00             	jmp    0x1bd8
    1b86:	c4 5e 04             	les    0x4(%bp),%bx
    1b89:	26 c7 87 9e 10 ff ff 	movw   $0xffff,%es:0x109e(%bx)
    1b90:	c4 5e 04             	les    0x4(%bp),%bx
    1b93:	26 80 bf 50 02 00    	cmpb   $0x0,%es:0x250(%bx)
    1b99:	75 03                	jne    0x1b9e
    1b9b:	e9 34 00             	jmp    0x1bd2
    1b9e:	8b 46 04             	mov    0x4(%bp),%ax
    1ba1:	8b 56 06             	mov    0x6(%bp),%dx
    1ba4:	05 50 02             	add    $0x250,%ax
    1ba7:	52                   	push   %dx
    1ba8:	50                   	push   %ax
    1ba9:	8b 46 04             	mov    0x4(%bp),%ax
    1bac:	8b 56 06             	mov    0x6(%bp),%dx
    1baf:	05 a0 10             	add    $0x10a0,%ax
    1bb2:	52                   	push   %dx
    1bb3:	50                   	push   %ax
    1bb4:	b8 00 02             	mov    $0x200,%ax
    1bb7:	50                   	push   %ax
    1bb8:	9a ff ff 00 00       	lcall  $0x0,$0xffff
    1bbd:	40                   	inc    %ax
    1bbe:	74 03                	je     0x1bc3
    1bc0:	e9 06 00             	jmp    0x1bc9
    1bc3:	b8 00 00             	mov    $0x0,%ax
    1bc6:	e9 0f 00             	jmp    0x1bd8
    1bc9:	c4 5e 04             	les    0x4(%bp),%bx
    1bcc:	26 c6 87 50 02 00    	movb   $0x0,%es:0x250(%bx)
    1bd2:	b8 01 00             	mov    $0x1,%ax
    1bd5:	e9 00 00             	jmp    0x1bd8
    1bd8:	5e                   	pop    %si
    1bd9:	5f                   	pop    %di
    1bda:	8b e5                	mov    %bp,%sp
    1bdc:	5d                   	pop    %bp
    1bdd:	c3                   	ret
    1bde:	55                   	push   %bp
    1bdf:	8b ec                	mov    %sp,%bp
    1be1:	81 ec 08 00          	sub    $0x8,%sp
    1be5:	57                   	push   %di
    1be6:	56                   	push   %si
    1be7:	83 7e 08 75          	cmpw   $0x75,0x8(%bp)
    1beb:	77 03                	ja     0x1bf0
    1bed:	e9 06 00             	jmp    0x1bf6
    1bf0:	b8 00 00             	mov    $0x0,%ax
    1bf3:	e9 18 01             	jmp    0x1d0e
    1bf6:	c7 46 fa 00 00       	movw   $0x0,-0x6(%bp)
    1bfb:	e9 03 00             	jmp    0x1c01
    1bfe:	ff 46 fa             	incw   -0x6(%bp)
    1c01:	8b 46 08             	mov    0x8(%bp),%ax
    1c04:	39 46 fa             	cmp    %ax,-0x6(%bp)
    1c07:	72 03                	jb     0x1c0c
    1c09:	e9 1b 00             	jmp    0x1c27
    1c0c:	c4 5e 04             	les    0x4(%bp),%bx
    1c0f:	81 c3 d0 01          	add    $0x1d0,%bx
    1c13:	8b 76 fa             	mov    -0x6(%bp),%si
    1c16:	26 8a 00             	mov    %es:(%bx,%si),%al
    1c19:	c4 5e 04             	les    0x4(%bp),%bx
    1c1c:	8b 76 fa             	mov    -0x6(%bp),%si
    1c1f:	26 88 80 50 01       	mov    %al,%es:0x150(%bx,%si)
    1c24:	e9 d7 ff             	jmp    0x1bfe
    1c27:	c4 5e 04             	les    0x4(%bp),%bx
    1c2a:	8b 76 08             	mov    0x8(%bp),%si
    1c2d:	26 c6 80 50 01 43    	movb   $0x43,%es:0x150(%bx,%si)
    1c33:	c4 5e 04             	les    0x4(%bp),%bx
    1c36:	8b 76 08             	mov    0x8(%bp),%si
    1c39:	26 c6 80 51 01 44    	movb   $0x44,%es:0x151(%bx,%si)
    1c3f:	c7 46 fa 00 00       	movw   $0x0,-0x6(%bp)
    1c44:	e9 03 00             	jmp    0x1c4a
    1c47:	ff 46 fa             	incw   -0x6(%bp)
    1c4a:	83 7e fa 10          	cmpw   $0x10,-0x6(%bp)
    1c4e:	72 03                	jb     0x1c53
    1c50:	e9 b5 00             	jmp    0x1d08
    1c53:	9a ff ff 00 00       	lcall  $0x0,$0xffff
    1c58:	03 46 fa             	add    -0x6(%bp),%ax
    1c5b:	89 46 fc             	mov    %ax,-0x4(%bp)
    1c5e:	c7 46 f8 00 00       	movw   $0x0,-0x8(%bp)
    1c63:	e9 03 00             	jmp    0x1c69
    1c66:	ff 46 f8             	incw   -0x8(%bp)
    1c69:	83 7e f8 04          	cmpw   $0x4,-0x8(%bp)
    1c6d:	72 03                	jb     0x1c72
    1c6f:	e9 20 00             	jmp    0x1c92
    1c72:	8a 5e fc             	mov    -0x4(%bp),%bl
    1c75:	83 e3 0f             	and    $0xf,%bx
    1c78:	8a 87 e0 00          	mov    0xe0(%bx),%al
    1c7c:	c4 5e 04             	les    0x4(%bp),%bx
    1c7f:	2b 5e f8             	sub    -0x8(%bp),%bx
    1c82:	8b 76 08             	mov    0x8(%bp),%si
    1c85:	26 88 80 55 01       	mov    %al,%es:0x155(%bx,%si)
    1c8a:	b1 04                	mov    $0x4,%cl
    1c8c:	d3 6e fc             	shrw   %cl,-0x4(%bp)
    1c8f:	e9 d4 ff             	jmp    0x1c66
    1c92:	b8 05 00             	mov    $0x5,%ax
    1c95:	50                   	push   %ax
    1c96:	b8 da 00             	mov    $0xda,%ax
    1c99:	1e                   	push   %ds
    1c9a:	50                   	push   %ax
    1c9b:	8b 46 04             	mov    0x4(%bp),%ax
    1c9e:	8b 56 06             	mov    0x6(%bp),%dx
    1ca1:	03 46 08             	add    0x8(%bp),%ax
    1ca4:	05 56 01             	add    $0x156,%ax
    1ca7:	52                   	push   %dx
    1ca8:	50                   	push   %ax
    1ca9:	e8 80 e5             	call   0x22c
    1cac:	83 c4 0a             	add    $0xa,%sp
    1caf:	8b 46 04             	mov    0x4(%bp),%ax
    1cb2:	8b 56 06             	mov    0x6(%bp),%dx
    1cb5:	05 50 01             	add    $0x150,%ax
    1cb8:	52                   	push   %dx
    1cb9:	50                   	push   %ax
    1cba:	9a ff ff 00 00       	lcall  $0x0,$0xffff
    1cbf:	89 46 fe             	mov    %ax,-0x2(%bp)
    1cc2:	83 7e fe ff          	cmpw   $0xffff,-0x2(%bp)
    1cc6:	75 03                	jne    0x1ccb
    1cc8:	e9 3a 00             	jmp    0x1d05
    1ccb:	b8 80 00             	mov    $0x80,%ax
    1cce:	50                   	push   %ax
    1ccf:	8b 46 04             	mov    0x4(%bp),%ax
    1cd2:	8b 56 06             	mov    0x6(%bp),%dx
    1cd5:	05 50 01             	add    $0x150,%ax
    1cd8:	52                   	push   %dx
    1cd9:	50                   	push   %ax
    1cda:	8b 46 04             	mov    0x4(%bp),%ax
    1cdd:	8b 56 06             	mov    0x6(%bp),%dx
    1ce0:	05 50 02             	add    $0x250,%ax
    1ce3:	52                   	push   %dx
    1ce4:	50                   	push   %ax
    1ce5:	e8 44 e5             	call   0x22c
    1ce8:	83 c4 0a             	add    $0xa,%sp
    1ceb:	8b 46 fe             	mov    -0x2(%bp),%ax
    1cee:	c4 5e 04             	les    0x4(%bp),%bx
    1cf1:	26 89 87 9e 10       	mov    %ax,%es:0x109e(%bx)
    1cf6:	ff 76 06             	push   0x6(%bp)
    1cf9:	ff 76 04             	push   0x4(%bp)
    1cfc:	e8 57 fe             	call   0x1b56
    1cff:	83 c4 04             	add    $0x4,%sp
    1d02:	e9 09 00             	jmp    0x1d0e
    1d05:	e9 3f ff             	jmp    0x1c47
    1d08:	b8 00 00             	mov    $0x0,%ax
    1d0b:	e9 00 00             	jmp    0x1d0e
    1d0e:	5e                   	pop    %si
    1d0f:	5f                   	pop    %di
    1d10:	8b e5                	mov    %bp,%sp
    1d12:	5d                   	pop    %bp
    1d13:	c3                   	ret
    1d14:	55                   	push   %bp
    1d15:	8b ec                	mov    %sp,%bp
    1d17:	81 ec 18 00          	sub    $0x18,%sp
    1d1b:	57                   	push   %di
    1d1c:	56                   	push   %si
    1d1d:	b8 00 00             	mov    $0x0,%ax
    1d20:	89 46 ee             	mov    %ax,-0x12(%bp)
    1d23:	89 46 f8             	mov    %ax,-0x8(%bp)
    1d26:	c4 5e 06             	les    0x6(%bp),%bx
    1d29:	26 8b 47 34          	mov    %es:0x34(%bx),%ax
    1d2d:	26 8b 57 36          	mov    %es:0x36(%bx),%dx
    1d31:	89 46 fc             	mov    %ax,-0x4(%bp)
    1d34:	89 56 fe             	mov    %dx,-0x2(%bp)
    1d37:	ff 76 04             	push   0x4(%bp)
    1d3a:	b8 64 00             	mov    $0x64,%ax
    1d3d:	50                   	push   %ax
    1d3e:	8b 46 06             	mov    0x6(%bp),%ax
    1d41:	8b 56 08             	mov    0x8(%bp),%dx
    1d44:	05 50 00             	add    $0x50,%ax
    1d47:	52                   	push   %dx
    1d48:	50                   	push   %ax
    1d49:	b8 80 00             	mov    $0x80,%ax
    1d4c:	50                   	push   %ax
    1d4d:	9a ff ff 00 00       	lcall  $0x0,$0xffff
    1d52:	b8 80 00             	mov    $0x80,%ax
    1d55:	50                   	push   %ax
    1d56:	8b 46 06             	mov    0x6(%bp),%ax
    1d59:	8b 56 08             	mov    0x8(%bp),%dx
    1d5c:	05 50 00             	add    $0x50,%ax
    1d5f:	52                   	push   %dx
    1d60:	50                   	push   %ax
    1d61:	e8 55 e4             	call   0x1b9
    1d64:	83 c4 06             	add    $0x6,%sp
    1d67:	89 46 ec             	mov    %ax,-0x14(%bp)
    1d6a:	83 7e ec 00          	cmpw   $0x0,-0x14(%bp)
    1d6e:	74 03                	je     0x1d73
    1d70:	e9 14 00             	jmp    0x1d87
    1d73:	b8 f1 00             	mov    $0xf1,%ax
    1d76:	1e                   	push   %ds
    1d77:	50                   	push   %ax
    1d78:	ff 76 04             	push   0x4(%bp)
    1d7b:	e8 b1 fd             	call   0x1b2f
    1d7e:	83 c4 06             	add    $0x6,%sp
    1d81:	b8 00 00             	mov    $0x0,%ax
    1d84:	e9 e7 09             	jmp    0x276e
    1d87:	c7 46 f6 00 00       	movw   $0x0,-0xa(%bp)
    1d8c:	e9 03 00             	jmp    0x1d92
    1d8f:	ff 46 f6             	incw   -0xa(%bp)
    1d92:	8b 46 ec             	mov    -0x14(%bp),%ax
    1d95:	39 46 f6             	cmp    %ax,-0xa(%bp)
    1d98:	72 03                	jb     0x1d9d
    1d9a:	e9 20 00             	jmp    0x1dbd
    1d9d:	c4 5e 06             	les    0x6(%bp),%bx
    1da0:	83 c3 50             	add    $0x50,%bx
    1da3:	8b 76 f6             	mov    -0xa(%bp),%si
    1da6:	26 80 38 2f          	cmpb   $0x2f,%es:(%bx,%si)
    1daa:	74 03                	je     0x1daf
    1dac:	e9 0b 00             	jmp    0x1dba
    1daf:	c4 5e 06             	les    0x6(%bp),%bx
    1db2:	8b 76 f6             	mov    -0xa(%bp),%si
    1db5:	26 c6 40 50 5c       	movb   $0x5c,%es:0x50(%bx,%si)
    1dba:	e9 d2 ff             	jmp    0x1d8f
    1dbd:	83 7e ec 01          	cmpw   $0x1,-0x14(%bp)
    1dc1:	77 03                	ja     0x1dc6
    1dc3:	e9 2e 00             	jmp    0x1df4
    1dc6:	c4 5e 06             	les    0x6(%bp),%bx
    1dc9:	26 80 7f 50 5c       	cmpb   $0x5c,%es:0x50(%bx)
    1dce:	74 03                	je     0x1dd3
    1dd0:	e9 21 00             	jmp    0x1df4
    1dd3:	c4 5e 06             	les    0x6(%bp),%bx
    1dd6:	26 80 7f 51 5c       	cmpb   $0x5c,%es:0x51(%bx)
    1ddb:	74 03                	je     0x1de0
    1ddd:	e9 14 00             	jmp    0x1df4
    1de0:	b8 02 01             	mov    $0x102,%ax
    1de3:	1e                   	push   %ds
    1de4:	50                   	push   %ax
    1de5:	ff 76 04             	push   0x4(%bp)
    1de8:	e8 44 fd             	call   0x1b2f
    1deb:	83 c4 06             	add    $0x6,%sp
    1dee:	b8 00 00             	mov    $0x0,%ax
    1df1:	e9 7a 09             	jmp    0x276e
    1df4:	8b 46 06             	mov    0x6(%bp),%ax
    1df7:	8b 56 08             	mov    0x8(%bp),%dx
    1dfa:	05 50 00             	add    $0x50,%ax
    1dfd:	52                   	push   %dx
    1dfe:	50                   	push   %ax
    1dff:	9a ff ff 00 00       	lcall  $0x0,$0xffff
    1e04:	89 46 f2             	mov    %ax,-0xe(%bp)
    1e07:	83 7e f2 00          	cmpw   $0x0,-0xe(%bp)
    1e0b:	7d 03                	jge    0x1e10
    1e0d:	e9 5f 00             	jmp    0x1e6f
    1e10:	f6 46 f2 10          	testb  $0x10,-0xe(%bp)
    1e14:	75 03                	jne    0x1e19
    1e16:	e9 56 00             	jmp    0x1e6f
    1e19:	8b 46 06             	mov    0x6(%bp),%ax
    1e1c:	8b 56 08             	mov    0x8(%bp),%dx
    1e1f:	05 50 00             	add    $0x50,%ax
    1e22:	52                   	push   %dx
    1e23:	50                   	push   %ax
    1e24:	ff 76 08             	push   0x8(%bp)
    1e27:	ff 76 06             	push   0x6(%bp)
    1e2a:	e8 49 ec             	call   0xa76
    1e2d:	83 c4 08             	add    $0x8,%sp
    1e30:	3d 00 00             	cmp    $0x0,%ax
    1e33:	75 03                	jne    0x1e38
    1e35:	e9 23 00             	jmp    0x1e5b
    1e38:	ff 76 04             	push   0x4(%bp)
    1e3b:	b8 64 00             	mov    $0x64,%ax
    1e3e:	50                   	push   %ax
    1e3f:	b8 13 01             	mov    $0x113,%ax
    1e42:	1e                   	push   %ds
    1e43:	50                   	push   %ax
    1e44:	9a b1 1e 00 00       	lcall  $0x0,$0x1eb1
    1e49:	ff 76 08             	push   0x8(%bp)
    1e4c:	ff 76 06             	push   0x6(%bp)
    1e4f:	ff 76 04             	push   0x4(%bp)
    1e52:	e8 88 f4             	call   0x12dd
    1e55:	83 c4 06             	add    $0x6,%sp
    1e58:	e9 0e 00             	jmp    0x1e69
    1e5b:	b8 14 01             	mov    $0x114,%ax
    1e5e:	1e                   	push   %ds
    1e5f:	50                   	push   %ax
    1e60:	ff 76 04             	push   0x4(%bp)
    1e63:	e8 c9 fc             	call   0x1b2f
    1e66:	83 c4 06             	add    $0x6,%sp
    1e69:	b8 00 00             	mov    $0x0,%ax
    1e6c:	e9 ff 08             	jmp    0x276e
    1e6f:	83 7e ec 02          	cmpw   $0x2,-0x14(%bp)
    1e73:	74 03                	je     0x1e78
    1e75:	e9 63 00             	jmp    0x1edb
    1e78:	c4 5e 06             	les    0x6(%bp),%bx
    1e7b:	26 80 7f 51 3a       	cmpb   $0x3a,%es:0x51(%bx)
    1e80:	74 03                	je     0x1e85
    1e82:	e9 56 00             	jmp    0x1edb
    1e85:	8b 46 06             	mov    0x6(%bp),%ax
    1e88:	8b 56 08             	mov    0x8(%bp),%dx
    1e8b:	05 50 00             	add    $0x50,%ax
    1e8e:	52                   	push   %dx
    1e8f:	50                   	push   %ax
    1e90:	ff 76 08             	push   0x8(%bp)
    1e93:	ff 76 06             	push   0x6(%bp)
    1e96:	e8 dd eb             	call   0xa76
    1e99:	83 c4 08             	add    $0x8,%sp
    1e9c:	3d 00 00             	cmp    $0x0,%ax
    1e9f:	75 03                	jne    0x1ea4
    1ea1:	e9 23 00             	jmp    0x1ec7
    1ea4:	ff 76 04             	push   0x4(%bp)
    1ea7:	b8 64 00             	mov    $0x64,%ax
    1eaa:	50                   	push   %ax
    1eab:	b8 23 01             	mov    $0x123,%ax
    1eae:	1e                   	push   %ds
    1eaf:	50                   	push   %ax
    1eb0:	9a ff ff 00 00       	lcall  $0x0,$0xffff
    1eb5:	ff 76 08             	push   0x8(%bp)
    1eb8:	ff 76 06             	push   0x6(%bp)
    1ebb:	ff 76 04             	push   0x4(%bp)
    1ebe:	e8 1c f4             	call   0x12dd
    1ec1:	83 c4 06             	add    $0x6,%sp
    1ec4:	e9 0e 00             	jmp    0x1ed5
    1ec7:	b8 24 01             	mov    $0x124,%ax
    1eca:	1e                   	push   %ds
    1ecb:	50                   	push   %ax
    1ecc:	ff 76 04             	push   0x4(%bp)
    1ecf:	e8 5d fc             	call   0x1b2f
    1ed2:	83 c4 06             	add    $0x6,%sp
    1ed5:	b8 00 00             	mov    $0x0,%ax
    1ed8:	e9 93 08             	jmp    0x276e
    1edb:	8b 46 06             	mov    0x6(%bp),%ax
    1ede:	8b 56 08             	mov    0x8(%bp),%dx
    1ee1:	05 50 00             	add    $0x50,%ax
    1ee4:	52                   	push   %dx
    1ee5:	50                   	push   %ax
    1ee6:	e8 10 f5             	call   0x13f9
    1ee9:	83 c4 04             	add    $0x4,%sp
    1eec:	3d 00 00             	cmp    $0x0,%ax
    1eef:	75 03                	jne    0x1ef4
    1ef1:	e9 cc 00             	jmp    0x1fc0
    1ef4:	83 7e ec 40          	cmpw   $0x40,-0x14(%bp)
    1ef8:	72 03                	jb     0x1efd
    1efa:	e9 1d 00             	jmp    0x1f1a
    1efd:	b8 01 00             	mov    $0x1,%ax
    1f00:	50                   	push   %ax
    1f01:	8b 46 06             	mov    0x6(%bp),%ax
    1f04:	8b 56 08             	mov    0x8(%bp),%dx
    1f07:	05 50 00             	add    $0x50,%ax
    1f0a:	52                   	push   %dx
    1f0b:	50                   	push   %ax
    1f0c:	e8 d1 e5             	call   0x4e0
    1f0f:	83 c4 06             	add    $0x6,%sp
    1f12:	3d 00 00             	cmp    $0x0,%ax
    1f15:	74 03                	je     0x1f1a
    1f17:	e9 14 00             	jmp    0x1f2e
    1f1a:	b8 37 01             	mov    $0x137,%ax
    1f1d:	1e                   	push   %ds
    1f1e:	50                   	push   %ax
    1f1f:	ff 76 04             	push   0x4(%bp)
    1f22:	e8 0a fc             	call   0x1b2f
    1f25:	83 c4 06             	add    $0x6,%sp
    1f28:	b8 00 00             	mov    $0x0,%ax
    1f2b:	e9 40 08             	jmp    0x276e
    1f2e:	c7 46 f6 00 00       	movw   $0x0,-0xa(%bp)
    1f33:	e9 03 00             	jmp    0x1f39
    1f36:	ff 46 f6             	incw   -0xa(%bp)
    1f39:	8b 46 ec             	mov    -0x14(%bp),%ax
    1f3c:	39 46 f6             	cmp    %ax,-0xa(%bp)
    1f3f:	72 03                	jb     0x1f44
    1f41:	e9 3b 00             	jmp    0x1f7f
    1f44:	c4 5e 06             	les    0x6(%bp),%bx
    1f47:	83 c3 50             	add    $0x50,%bx
    1f4a:	8b 76 f6             	mov    -0xa(%bp),%si
    1f4d:	26 80 38 5c          	cmpb   $0x5c,%es:(%bx,%si)
    1f51:	75 03                	jne    0x1f56
    1f53:	e9 12 00             	jmp    0x1f68
    1f56:	c4 5e 06             	les    0x6(%bp),%bx
    1f59:	83 c3 50             	add    $0x50,%bx
    1f5c:	8b 76 f6             	mov    -0xa(%bp),%si
    1f5f:	26 80 38 3a          	cmpb   $0x3a,%es:(%bx,%si)
    1f63:	74 03                	je     0x1f68
    1f65:	e9 14 00             	jmp    0x1f7c
    1f68:	b8 44 01             	mov    $0x144,%ax
    1f6b:	1e                   	push   %ds
    1f6c:	50                   	push   %ax
    1f6d:	ff 76 04             	push   0x4(%bp)
    1f70:	e8 bc fb             	call   0x1b2f
    1f73:	83 c4 06             	add    $0x6,%sp
    1f76:	b8 00 00             	mov    $0x0,%ax
    1f79:	e9 f2 07             	jmp    0x276e
    1f7c:	e9 b7 ff             	jmp    0x1f36
    1f7f:	b8 40 00             	mov    $0x40,%ax
    1f82:	50                   	push   %ax
    1f83:	8b 46 06             	mov    0x6(%bp),%ax
    1f86:	8b 56 08             	mov    0x8(%bp),%dx
    1f89:	05 50 00             	add    $0x50,%ax
    1f8c:	52                   	push   %dx
    1f8d:	50                   	push   %ax
    1f8e:	b1 06                	mov    $0x6,%cl
    1f90:	c4 5e 06             	les    0x6(%bp),%bx
    1f93:	26 8b 87 96 09       	mov    %es:0x996(%bx),%ax
    1f98:	d3 e0                	shl    %cl,%ax
    1f9a:	03 46 06             	add    0x6(%bp),%ax
    1f9d:	8b 56 08             	mov    0x8(%bp),%dx
    1fa0:	05 14 03             	add    $0x314,%ax
    1fa3:	52                   	push   %dx
    1fa4:	50                   	push   %ax
    1fa5:	e8 84 e2             	call   0x22c
    1fa8:	83 c4 0a             	add    $0xa,%sp
    1fab:	ff 76 08             	push   0x8(%bp)
    1fae:	ff 76 06             	push   0x6(%bp)
    1fb1:	ff 76 04             	push   0x4(%bp)
    1fb4:	e8 26 f3             	call   0x12dd
    1fb7:	83 c4 06             	add    $0x6,%sp
    1fba:	b8 00 00             	mov    $0x0,%ax
    1fbd:	e9 ae 07             	jmp    0x276e
    1fc0:	b8 00 00             	mov    $0x0,%ax
    1fc3:	50                   	push   %ax
    1fc4:	8b 4e 06             	mov    0x6(%bp),%cx
    1fc7:	8b 56 08             	mov    0x8(%bp),%dx
    1fca:	83 c1 50             	add    $0x50,%cx
    1fcd:	52                   	push   %dx
    1fce:	51                   	push   %cx
    1fcf:	e8 0e e5             	call   0x4e0
    1fd2:	83 c4 06             	add    $0x6,%sp
    1fd5:	3d 00 00             	cmp    $0x0,%ax
    1fd8:	74 03                	je     0x1fdd
    1fda:	e9 14 00             	jmp    0x1ff1
    1fdd:	b8 56 01             	mov    $0x156,%ax
    1fe0:	1e                   	push   %ds
    1fe1:	50                   	push   %ax
    1fe2:	ff 76 04             	push   0x4(%bp)
    1fe5:	e8 47 fb             	call   0x1b2f
    1fe8:	83 c4 06             	add    $0x6,%sp
    1feb:	b8 00 00             	mov    $0x0,%ax
    1fee:	e9 7d 07             	jmp    0x276e
    1ff1:	c4 5e 06             	les    0x6(%bp),%bx
    1ff4:	8b 76 ec             	mov    -0x14(%bp),%si
    1ff7:	26 80 78 4f 2e       	cmpb   $0x2e,%es:0x4f(%bx,%si)
    1ffc:	74 03                	je     0x2001
    1ffe:	e9 06 00             	jmp    0x2007
    2001:	b8 01 00             	mov    $0x1,%ax
    2004:	e9 03 00             	jmp    0x200a
    2007:	b8 00 00             	mov    $0x0,%ax
    200a:	89 46 f4             	mov    %ax,-0xc(%bp)
    200d:	c7 46 f6 00 00       	movw   $0x0,-0xa(%bp)
    2012:	e9 03 00             	jmp    0x2018
    2015:	ff 46 f6             	incw   -0xa(%bp)
    2018:	8b 46 ec             	mov    -0x14(%bp),%ax
    201b:	39 46 f6             	cmp    %ax,-0xa(%bp)
    201e:	72 03                	jb     0x2023
    2020:	e9 4e 00             	jmp    0x2071
    2023:	c4 5e 06             	les    0x6(%bp),%bx
    2026:	83 c3 50             	add    $0x50,%bx
    2029:	8b 76 f6             	mov    -0xa(%bp),%si
    202c:	26 80 38 5c          	cmpb   $0x5c,%es:(%bx,%si)
    2030:	75 03                	jne    0x2035
    2032:	e9 12 00             	jmp    0x2047
    2035:	c4 5e 06             	les    0x6(%bp),%bx
    2038:	83 c3 50             	add    $0x50,%bx
    203b:	8b 76 f6             	mov    -0xa(%bp),%si
    203e:	26 80 38 3a          	cmpb   $0x3a,%es:(%bx,%si)
    2042:	74 03                	je     0x2047
    2044:	e9 0f 00             	jmp    0x2056
    2047:	8b 46 f6             	mov    -0xa(%bp),%ax
    204a:	40                   	inc    %ax
    204b:	89 46 ee             	mov    %ax,-0x12(%bp)
    204e:	c7 46 f8 00 00       	movw   $0x0,-0x8(%bp)
    2053:	e9 18 00             	jmp    0x206e
    2056:	c4 5e 06             	les    0x6(%bp),%bx
    2059:	83 c3 50             	add    $0x50,%bx
    205c:	8b 76 f6             	mov    -0xa(%bp),%si
    205f:	26 80 38 2e          	cmpb   $0x2e,%es:(%bx,%si)
    2063:	74 03                	je     0x2068
    2065:	e9 06 00             	jmp    0x206e
    2068:	8b 46 f6             	mov    -0xa(%bp),%ax
    206b:	89 46 f8             	mov    %ax,-0x8(%bp)
    206e:	e9 a4 ff             	jmp    0x2015
    2071:	83 7e f8 00          	cmpw   $0x0,-0x8(%bp)
    2075:	74 03                	je     0x207a
    2077:	e9 99 00             	jmp    0x2113
    207a:	c4 5e 06             	les    0x6(%bp),%bx
    207d:	26 80 bf 10 03 00    	cmpb   $0x0,%es:0x310(%bx)
    2083:	75 03                	jne    0x2088
    2085:	e9 8b 00             	jmp    0x2113
    2088:	b8 04 00             	mov    $0x4,%ax
    208b:	50                   	push   %ax
    208c:	8b 46 06             	mov    0x6(%bp),%ax
    208f:	8b 56 08             	mov    0x8(%bp),%dx
    2092:	05 10 03             	add    $0x310,%ax
    2095:	52                   	push   %dx
    2096:	50                   	push   %ax
    2097:	e8 1f e1             	call   0x1b9
    209a:	83 c4 06             	add    $0x6,%sp
    209d:	89 46 f0             	mov    %ax,-0x10(%bp)
    20a0:	03 46 ec             	add    -0x14(%bp),%ax
    20a3:	40                   	inc    %ax
    20a4:	3d 80 00             	cmp    $0x80,%ax
    20a7:	73 03                	jae    0x20ac
    20a9:	e9 26 00             	jmp    0x20d2
    20ac:	b8 02 30             	mov    $0x3002,%ax
    20af:	ba 00 00             	mov    $0x0,%dx
    20b2:	52                   	push   %dx
    20b3:	50                   	push   %ax
    20b4:	ff 76 08             	push   0x8(%bp)
    20b7:	ff 76 06             	push   0x6(%bp)
    20ba:	e8 e2 e8             	call   0x99f
    20bd:	83 c4 08             	add    $0x8,%sp
    20c0:	ff 76 04             	push   0x4(%bp)
    20c3:	b8 00 00             	mov    $0x0,%ax
    20c6:	50                   	push   %ax
    20c7:	9a 0a 17 00 00       	lcall  $0x0,$0x170a
    20cc:	b8 00 00             	mov    $0x0,%ax
    20cf:	e9 9c 06             	jmp    0x276e
    20d2:	c4 5e 06             	les    0x6(%bp),%bx
    20d5:	8b 76 ec             	mov    -0x14(%bp),%si
    20d8:	26 c6 40 50 2e       	movb   $0x2e,%es:0x50(%bx,%si)
    20dd:	ff 46 ec             	incw   -0x14(%bp)
    20e0:	c7 46 f6 00 00       	movw   $0x0,-0xa(%bp)
    20e5:	e9 03 00             	jmp    0x20eb
    20e8:	ff 46 f6             	incw   -0xa(%bp)
    20eb:	8b 46 f6             	mov    -0xa(%bp),%ax
    20ee:	39 46 f0             	cmp    %ax,-0x10(%bp)
    20f1:	73 03                	jae    0x20f6
    20f3:	e9 1d 00             	jmp    0x2113
    20f6:	c4 5e 06             	les    0x6(%bp),%bx
    20f9:	81 c3 10 03          	add    $0x310,%bx
    20fd:	8b 76 f6             	mov    -0xa(%bp),%si
    2100:	26 8a 00             	mov    %es:(%bx,%si),%al
    2103:	c4 5e 06             	les    0x6(%bp),%bx
    2106:	03 5e f6             	add    -0xa(%bp),%bx
    2109:	8b 76 ec             	mov    -0x14(%bp),%si
    210c:	26 88 40 50          	mov    %al,%es:0x50(%bx,%si)
    2110:	e9 d5 ff             	jmp    0x20e8
    2113:	8b 46 06             	mov    0x6(%bp),%ax
    2116:	8b 56 08             	mov    0x8(%bp),%dx
    2119:	05 50 00             	add    $0x50,%ax
    211c:	52                   	push   %dx
    211d:	50                   	push   %ax
    211e:	8b 46 06             	mov    0x6(%bp),%ax
    2121:	8b 56 08             	mov    0x8(%bp),%dx
    2124:	05 a0 10             	add    $0x10a0,%ax
    2127:	52                   	push   %dx
    2128:	50                   	push   %ax
    2129:	b8 00 01             	mov    $0x100,%ax
    212c:	50                   	push   %ax
    212d:	9a b9 1b 00 00       	lcall  $0x0,$0x1bb9
    2132:	40                   	inc    %ax
    2133:	75 03                	jne    0x2138
    2135:	e9 1e 00             	jmp    0x2156
    2138:	b8 00 00             	mov    $0x0,%ax
    213b:	50                   	push   %ax
    213c:	8b 4e 06             	mov    0x6(%bp),%cx
    213f:	8b 56 08             	mov    0x8(%bp),%dx
    2142:	81 c1 a8 10          	add    $0x10a8,%cx
    2146:	52                   	push   %dx
    2147:	51                   	push   %cx
    2148:	e8 95 e3             	call   0x4e0
    214b:	83 c4 06             	add    $0x6,%sp
    214e:	3d 00 00             	cmp    $0x0,%ax
    2151:	74 03                	je     0x2156
    2153:	e9 14 00             	jmp    0x216a
    2156:	b8 68 01             	mov    $0x168,%ax
    2159:	1e                   	push   %ds
    215a:	50                   	push   %ax
    215b:	ff 76 04             	push   0x4(%bp)
    215e:	e8 ce f9             	call   0x1b2f
    2161:	83 c4 06             	add    $0x6,%sp
    2164:	b8 00 00             	mov    $0x0,%ax
    2167:	e9 04 06             	jmp    0x276e
    216a:	b8 80 00             	mov    $0x80,%ax
    216d:	50                   	push   %ax
    216e:	8b 4e 06             	mov    0x6(%bp),%cx
    2171:	8b 56 08             	mov    0x8(%bp),%dx
    2174:	81 c1 a8 10          	add    $0x10a8,%cx
    2178:	52                   	push   %dx
    2179:	51                   	push   %cx
    217a:	8b 4e 06             	mov    0x6(%bp),%cx
    217d:	8b 56 08             	mov    0x8(%bp),%dx
    2180:	81 c1 d0 01          	add    $0x1d0,%cx
    2184:	52                   	push   %dx
    2185:	51                   	push   %cx
    2186:	e8 a3 e0             	call   0x22c
    2189:	83 c4 0a             	add    $0xa,%sp
    218c:	b8 80 00             	mov    $0x80,%ax
    218f:	50                   	push   %ax
    2190:	8b 46 06             	mov    0x6(%bp),%ax
    2193:	8b 56 08             	mov    0x8(%bp),%dx
    2196:	05 d0 01             	add    $0x1d0,%ax
    2199:	52                   	push   %dx
    219a:	50                   	push   %ax
    219b:	e8 1b e0             	call   0x1b9
    219e:	83 c4 06             	add    $0x6,%sp
    21a1:	89 46 ec             	mov    %ax,-0x14(%bp)
    21a4:	b8 00 00             	mov    $0x0,%ax
    21a7:	89 46 f8             	mov    %ax,-0x8(%bp)
    21aa:	89 46 ee             	mov    %ax,-0x12(%bp)
    21ad:	c7 46 f6 00 00       	movw   $0x0,-0xa(%bp)
    21b2:	e9 03 00             	jmp    0x21b8
    21b5:	ff 46 f6             	incw   -0xa(%bp)
    21b8:	8b 46 ec             	mov    -0x14(%bp),%ax
    21bb:	39 46 f6             	cmp    %ax,-0xa(%bp)
    21be:	72 03                	jb     0x21c3
    21c0:	e9 70 00             	jmp    0x2233
    21c3:	c4 5e 06             	les    0x6(%bp),%bx
    21c6:	81 c3 d0 01          	add    $0x1d0,%bx
    21ca:	8b 76 f6             	mov    -0xa(%bp),%si
    21cd:	26 8a 00             	mov    %es:(%bx,%si),%al
    21d0:	50                   	push   %ax
    21d1:	e8 b8 e0             	call   0x28c
    21d4:	83 c4 02             	add    $0x2,%sp
    21d7:	c4 5e 06             	les    0x6(%bp),%bx
    21da:	8b 76 f6             	mov    -0xa(%bp),%si
    21dd:	26 88 80 d0 01       	mov    %al,%es:0x1d0(%bx,%si)
    21e2:	c4 5e 06             	les    0x6(%bp),%bx
    21e5:	81 c3 d0 01          	add    $0x1d0,%bx
    21e9:	8b 76 f6             	mov    -0xa(%bp),%si
    21ec:	26 80 38 5c          	cmpb   $0x5c,%es:(%bx,%si)
    21f0:	75 03                	jne    0x21f5
    21f2:	e9 13 00             	jmp    0x2208
    21f5:	c4 5e 06             	les    0x6(%bp),%bx
    21f8:	81 c3 d0 01          	add    $0x1d0,%bx
    21fc:	8b 76 f6             	mov    -0xa(%bp),%si
    21ff:	26 80 38 3a          	cmpb   $0x3a,%es:(%bx,%si)
    2203:	74 03                	je     0x2208
    2205:	e9 0f 00             	jmp    0x2217
    2208:	8b 46 f6             	mov    -0xa(%bp),%ax
    220b:	40                   	inc    %ax
    220c:	89 46 ee             	mov    %ax,-0x12(%bp)
    220f:	c7 46 f8 00 00       	movw   $0x0,-0x8(%bp)
    2214:	e9 19 00             	jmp    0x2230
    2217:	c4 5e 06             	les    0x6(%bp),%bx
    221a:	81 c3 d0 01          	add    $0x1d0,%bx
    221e:	8b 76 f6             	mov    -0xa(%bp),%si
    2221:	26 80 38 2e          	cmpb   $0x2e,%es:(%bx,%si)
    2225:	74 03                	je     0x222a
    2227:	e9 06 00             	jmp    0x2230
    222a:	8b 46 f6             	mov    -0xa(%bp),%ax
    222d:	89 46 f8             	mov    %ax,-0x8(%bp)
    2230:	e9 82 ff             	jmp    0x21b5
    2233:	8b 46 06             	mov    0x6(%bp),%ax
    2236:	8b 56 08             	mov    0x8(%bp),%dx
    2239:	05 d0 01             	add    $0x1d0,%ax
    223c:	52                   	push   %dx
    223d:	50                   	push   %ax
    223e:	9a ac 22 00 00       	lcall  $0x0,$0x22ac
    2243:	89 46 f2             	mov    %ax,-0xe(%bp)
    2246:	b8 80 00             	mov    $0x80,%ax
    2249:	50                   	push   %ax
    224a:	8b 46 06             	mov    0x6(%bp),%ax
    224d:	8b 56 08             	mov    0x8(%bp),%dx
    2250:	05 d0 01             	add    $0x1d0,%ax
    2253:	52                   	push   %dx
    2254:	50                   	push   %ax
    2255:	8b 46 06             	mov    0x6(%bp),%ax
    2258:	8b 56 08             	mov    0x8(%bp),%dx
    225b:	05 d0 00             	add    $0xd0,%ax
    225e:	52                   	push   %dx
    225f:	50                   	push   %ax
    2260:	e8 c9 df             	call   0x22c
    2263:	83 c4 0a             	add    $0xa,%sp
    2266:	83 7e ee 03          	cmpw   $0x3,-0x12(%bp)
    226a:	77 03                	ja     0x226f
    226c:	e9 0f 00             	jmp    0x227e
    226f:	c4 5e 06             	les    0x6(%bp),%bx
    2272:	8b 76 ee             	mov    -0x12(%bp),%si
    2275:	26 c6 80 cf 00 00    	movb   $0x0,%es:0xcf(%bx,%si)
    227b:	e9 0c 00             	jmp    0x228a
    227e:	c4 5e 06             	les    0x6(%bp),%bx
    2281:	8b 76 ee             	mov    -0x12(%bp),%si
    2284:	26 c6 80 d0 00 00    	movb   $0x0,%es:0xd0(%bx,%si)
    228a:	f6 46 fd 38          	testb  $0x38,-0x3(%bp)
    228e:	74 03                	je     0x2293
    2290:	e9 0d 00             	jmp    0x22a0
    2293:	c4 5e 06             	les    0x6(%bp),%bx
    2296:	26 83 7f 4c 00       	cmpw   $0x0,%es:0x4c(%bx)
    229b:	75 03                	jne    0x22a0
    229d:	e9 38 00             	jmp    0x22d8
    22a0:	8b 46 06             	mov    0x6(%bp),%ax
    22a3:	8b 56 08             	mov    0x8(%bp),%dx
    22a6:	05 d0 00             	add    $0xd0,%ax
    22a9:	52                   	push   %dx
    22aa:	50                   	push   %ax
    22ab:	9a 00 1e 00 00       	lcall  $0x0,$0x1e00
    22b0:	89 46 f6             	mov    %ax,-0xa(%bp)
    22b3:	3d ff ff             	cmp    $0xffff,%ax
    22b6:	75 03                	jne    0x22bb
    22b8:	e9 09 00             	jmp    0x22c4
    22bb:	f6 46 f6 10          	testb  $0x10,-0xa(%bp)
    22bf:	74 03                	je     0x22c4
    22c1:	e9 14 00             	jmp    0x22d8
    22c4:	b8 72 01             	mov    $0x172,%ax
    22c7:	1e                   	push   %ds
    22c8:	50                   	push   %ax
    22c9:	ff 76 04             	push   0x4(%bp)
    22cc:	e8 60 f8             	call   0x1b2f
    22cf:	83 c4 06             	add    $0x6,%sp
    22d2:	b8 00 00             	mov    $0x0,%ax
    22d5:	e9 96 04             	jmp    0x276e
    22d8:	83 7e f2 00          	cmpw   $0x0,-0xe(%bp)
    22dc:	7c 03                	jl     0x22e1
    22de:	e9 26 00             	jmp    0x2307
    22e1:	f6 46 fd 10          	testb  $0x10,-0x3(%bp)
    22e5:	75 03                	jne    0x22ea
    22e7:	e9 1d 00             	jmp    0x2307
    22ea:	f6 46 fd 20          	testb  $0x20,-0x3(%bp)
    22ee:	74 03                	je     0x22f3
    22f0:	e9 14 00             	jmp    0x2307
    22f3:	b8 80 01             	mov    $0x180,%ax
    22f6:	1e                   	push   %ds
    22f7:	50                   	push   %ax
    22f8:	ff 76 04             	push   0x4(%bp)
    22fb:	e8 31 f8             	call   0x1b2f
    22fe:	83 c4 06             	add    $0x6,%sp
    2301:	b8 00 00             	mov    $0x0,%ax
    2304:	e9 67 04             	jmp    0x276e
    2307:	83 7e f2 00          	cmpw   $0x0,-0xe(%bp)
    230b:	7d 03                	jge    0x2310
    230d:	e9 1d 00             	jmp    0x232d
    2310:	f6 46 f2 10          	testb  $0x10,-0xe(%bp)
    2314:	75 03                	jne    0x2319
    2316:	e9 14 00             	jmp    0x232d
    2319:	b8 8e 01             	mov    $0x18e,%ax
    231c:	1e                   	push   %ds
    231d:	50                   	push   %ax
    231e:	ff 76 04             	push   0x4(%bp)
    2321:	e8 0b f8             	call   0x1b2f
    2324:	83 c4 06             	add    $0x6,%sp
    2327:	b8 00 00             	mov    $0x0,%ax
    232a:	e9 41 04             	jmp    0x276e
    232d:	83 7e f2 00          	cmpw   $0x0,-0xe(%bp)
    2331:	7d 03                	jge    0x2336
    2333:	e9 26 00             	jmp    0x235c
    2336:	f6 46 f2 01          	testb  $0x1,-0xe(%bp)
    233a:	75 03                	jne    0x233f
    233c:	e9 1d 00             	jmp    0x235c
    233f:	f6 46 fd 80          	testb  $0x80,-0x3(%bp)
    2343:	75 03                	jne    0x2348
    2345:	e9 14 00             	jmp    0x235c
    2348:	b8 9d 01             	mov    $0x19d,%ax
    234b:	1e                   	push   %ds
    234c:	50                   	push   %ax
    234d:	ff 76 04             	push   0x4(%bp)
    2350:	e8 dc f7             	call   0x1b2f
    2353:	83 c4 06             	add    $0x6,%sp
    2356:	b8 00 00             	mov    $0x0,%ax
    2359:	e9 12 04             	jmp    0x276e
    235c:	83 7e f2 00          	cmpw   $0x0,-0xe(%bp)
    2360:	7d 03                	jge    0x2365
    2362:	e9 41 00             	jmp    0x23a6
    2365:	c4 5e 06             	les    0x6(%bp),%bx
    2368:	26 83 7f 4c 00       	cmpw   $0x0,%es:0x4c(%bx)
    236d:	75 03                	jne    0x2372
    236f:	e9 34 00             	jmp    0x23a6
    2372:	f6 46 fc 02          	testb  $0x2,-0x4(%bp)
    2376:	75 03                	jne    0x237b
    2378:	e9 2b 00             	jmp    0x23a6
    237b:	b8 01 00             	mov    $0x1,%ax
    237e:	50                   	push   %ax
    237f:	8b 46 06             	mov    0x6(%bp),%ax
    2382:	8b 56 08             	mov    0x8(%bp),%dx
    2385:	05 d0 01             	add    $0x1d0,%ax
    2388:	52                   	push   %dx
    2389:	50                   	push   %ax
    238a:	b8 ad 01             	mov    $0x1ad,%ax
    238d:	1e                   	push   %ds
    238e:	50                   	push   %ax
    238f:	ff 76 04             	push   0x4(%bp)
    2392:	e8 f8 f4             	call   0x188d
    2395:	83 c4 0c             	add    $0xc,%sp
    2398:	3d 06 00             	cmp    $0x6,%ax
    239b:	75 03                	jne    0x23a0
    239d:	e9 06 00             	jmp    0x23a6
    23a0:	b8 00 00             	mov    $0x0,%ax
    23a3:	e9 c8 03             	jmp    0x276e
    23a6:	83 7e f2 00          	cmpw   $0x0,-0xe(%bp)
    23aa:	7c 03                	jl     0x23af
    23ac:	e9 34 00             	jmp    0x23e3
    23af:	f6 46 fd 20          	testb  $0x20,-0x3(%bp)
    23b3:	75 03                	jne    0x23b8
    23b5:	e9 2b 00             	jmp    0x23e3
    23b8:	b8 01 00             	mov    $0x1,%ax
    23bb:	50                   	push   %ax
    23bc:	8b 46 06             	mov    0x6(%bp),%ax
    23bf:	8b 56 08             	mov    0x8(%bp),%dx
    23c2:	05 d0 01             	add    $0x1d0,%ax
    23c5:	52                   	push   %dx
    23c6:	50                   	push   %ax
    23c7:	b8 bb 01             	mov    $0x1bb,%ax
    23ca:	1e                   	push   %ds
    23cb:	50                   	push   %ax
    23cc:	ff 76 04             	push   0x4(%bp)
    23cf:	e8 bb f4             	call   0x188d
    23d2:	83 c4 0c             	add    $0xc,%sp
    23d5:	3d 06 00             	cmp    $0x6,%ax
    23d8:	75 03                	jne    0x23dd
    23da:	e9 06 00             	jmp    0x23e3
    23dd:	b8 00 00             	mov    $0x0,%ax
    23e0:	e9 8b 03             	jmp    0x276e
    23e3:	83 7e f2 00          	cmpw   $0x0,-0xe(%bp)
    23e7:	7d 03                	jge    0x23ec
    23e9:	e9 5a 00             	jmp    0x2446
    23ec:	c4 5e 06             	les    0x6(%bp),%bx
    23ef:	26 83 7f 4c 00       	cmpw   $0x0,%es:0x4c(%bx)
    23f4:	74 03                	je     0x23f9
    23f6:	e9 09 00             	jmp    0x2402
    23f9:	f6 46 fd 80          	testb  $0x80,-0x3(%bp)
    23fd:	75 03                	jne    0x2402
    23ff:	e9 44 00             	jmp    0x2446
    2402:	8b 46 06             	mov    0x6(%bp),%ax
    2405:	8b 56 08             	mov    0x8(%bp),%dx
    2408:	05 d0 01             	add    $0x1d0,%ax
    240b:	52                   	push   %dx
    240c:	50                   	push   %ax
    240d:	8b 46 06             	mov    0x6(%bp),%ax
    2410:	8b 56 08             	mov    0x8(%bp),%dx
    2413:	05 a0 10             	add    $0x10a0,%ax
    2416:	52                   	push   %dx
    2417:	50                   	push   %ax
    2418:	b8 41 00             	mov    $0x41,%ax
    241b:	50                   	push   %ax
    241c:	9a 2e 21 00 00       	lcall  $0x0,$0x212e
    2421:	89 46 fa             	mov    %ax,-0x6(%bp)
    2424:	40                   	inc    %ax
    2425:	74 03                	je     0x242a
    2427:	e9 14 00             	jmp    0x243e
    242a:	b8 c8 01             	mov    $0x1c8,%ax
    242d:	1e                   	push   %ds
    242e:	50                   	push   %ax
    242f:	ff 76 04             	push   0x4(%bp)
    2432:	e8 fa f6             	call   0x1b2f
    2435:	83 c4 06             	add    $0x6,%sp
    2438:	b8 00 00             	mov    $0x0,%ax
    243b:	e9 30 03             	jmp    0x276e
    243e:	ff 76 fa             	push   -0x6(%bp)
    2441:	9a 76 1b 00 00       	lcall  $0x0,$0x1b76
    2446:	8b 46 ec             	mov    -0x14(%bp),%ax
    2449:	40                   	inc    %ax
    244a:	89 46 f0             	mov    %ax,-0x10(%bp)
    244d:	8b 46 f0             	mov    -0x10(%bp),%ax
    2450:	2b d2                	sub    %dx,%dx
    2452:	c4 5e 06             	les    0x6(%bp),%bx
    2455:	26 39 57 22          	cmp    %dx,%es:0x22(%bx)
    2459:	76 03                	jbe    0x245e
    245b:	e9 66 00             	jmp    0x24c4
    245e:	73 03                	jae    0x2463
    2460:	e9 09 00             	jmp    0x246c
    2463:	26 39 47 20          	cmp    %ax,%es:0x20(%bx)
    2467:	72 03                	jb     0x246c
    2469:	e9 58 00             	jmp    0x24c4
    246c:	c4 5e 06             	les    0x6(%bp),%bx
    246f:	26 83 7f 22 00       	cmpw   $0x0,%es:0x22(%bx)
    2474:	76 03                	jbe    0x2479
    2476:	e9 0a 00             	jmp    0x2483
    2479:	26 83 7f 20 02       	cmpw   $0x2,%es:0x20(%bx)
    247e:	73 03                	jae    0x2483
    2480:	e9 1b 00             	jmp    0x249e
    2483:	8a 46 f0             	mov    -0x10(%bp),%al
    2486:	c4 5e 06             	les    0x6(%bp),%bx
    2489:	26 c4 5f 1c          	les    %es:0x1c(%bx),%bx
    248d:	26 88 07             	mov    %al,%es:(%bx)
    2490:	8a 46 f1             	mov    -0xf(%bp),%al
    2493:	c4 5e 06             	les    0x6(%bp),%bx
    2496:	26 c4 5f 1c          	les    %es:0x1c(%bx),%bx
    249a:	26 88 47 01          	mov    %al,%es:0x1(%bx)
    249e:	b8 03 30             	mov    $0x3003,%ax
    24a1:	ba 00 00             	mov    $0x0,%dx
    24a4:	52                   	push   %dx
    24a5:	50                   	push   %ax
    24a6:	ff 76 08             	push   0x8(%bp)
    24a9:	ff 76 06             	push   0x6(%bp)
    24ac:	e8 f0 e4             	call   0x99f
    24af:	83 c4 08             	add    $0x8,%sp
    24b2:	ff 76 04             	push   0x4(%bp)
    24b5:	b8 00 00             	mov    $0x0,%ax
    24b8:	50                   	push   %ax
    24b9:	9a 55 25 00 00       	lcall  $0x0,$0x2555
    24be:	b8 00 00             	mov    $0x0,%ax
    24c1:	e9 aa 02             	jmp    0x276e
    24c4:	c4 5e 06             	les    0x6(%bp),%bx
    24c7:	26 83 7f 4c 00       	cmpw   $0x0,%es:0x4c(%bx)
    24cc:	75 03                	jne    0x24d1
    24ce:	e9 09 00             	jmp    0x24da
    24d1:	83 7e f2 00          	cmpw   $0x0,-0xe(%bp)
    24d5:	7d 03                	jge    0x24da
    24d7:	e9 09 00             	jmp    0x24e3
    24da:	f6 46 fd 80          	testb  $0x80,-0x3(%bp)
    24de:	75 03                	jne    0x24e3
    24e0:	e9 8d 00             	jmp    0x2570
    24e3:	ff 76 ee             	push   -0x12(%bp)
    24e6:	ff 76 08             	push   0x8(%bp)
    24e9:	ff 76 06             	push   0x6(%bp)
    24ec:	e8 ef f6             	call   0x1bde
    24ef:	83 c4 06             	add    $0x6,%sp
    24f2:	3d 00 00             	cmp    $0x0,%ax
    24f5:	74 03                	je     0x24fa
    24f7:	e9 76 00             	jmp    0x2570
    24fa:	c4 5e 06             	les    0x6(%bp),%bx
    24fd:	26 80 bf 50 02 00    	cmpb   $0x0,%es:0x250(%bx)
    2503:	75 03                	jne    0x2508
    2505:	e9 54 00             	jmp    0x255c
    2508:	b8 02 00             	mov    $0x2,%ax
    250b:	ba 00 00             	mov    $0x0,%dx
    250e:	52                   	push   %dx
    250f:	50                   	push   %ax
    2510:	ff 76 08             	push   0x8(%bp)
    2513:	ff 76 06             	push   0x6(%bp)
    2516:	e8 86 e4             	call   0x99f
    2519:	83 c4 08             	add    $0x8,%sp
    251c:	ff 76 08             	push   0x8(%bp)
    251f:	ff 76 06             	push   0x6(%bp)
    2522:	e8 31 f6             	call   0x1b56
    2525:	83 c4 04             	add    $0x4,%sp
    2528:	3d 00 00             	cmp    $0x0,%ax
    252b:	74 03                	je     0x2530
    252d:	e9 1d 00             	jmp    0x254d
    2530:	b8 00 00             	mov    $0x0,%ax
    2533:	50                   	push   %ax
    2534:	8b 46 06             	mov    0x6(%bp),%ax
    2537:	8b 56 08             	mov    0x8(%bp),%dx
    253a:	05 50 02             	add    $0x250,%ax
    253d:	52                   	push   %dx
    253e:	50                   	push   %ax
    253f:	b8 d6 01             	mov    $0x1d6,%ax
    2542:	1e                   	push   %ds
    2543:	50                   	push   %ax
    2544:	ff 76 04             	push   0x4(%bp)
    2547:	e8 43 f3             	call   0x188d
    254a:	83 c4 0c             	add    $0xc,%sp
    254d:	ff 76 04             	push   0x4(%bp)
    2550:	b8 00 00             	mov    $0x0,%ax
    2553:	50                   	push   %ax
    2554:	9a c8 20 00 00       	lcall  $0x0,$0x20c8
    2559:	e9 0e 00             	jmp    0x256a
    255c:	b8 eb 01             	mov    $0x1eb,%ax
    255f:	1e                   	push   %ds
    2560:	50                   	push   %ax
    2561:	ff 76 04             	push   0x4(%bp)
    2564:	e8 c8 f5             	call   0x1b2f
    2567:	83 c4 06             	add    $0x6,%sp
    256a:	b8 00 00             	mov    $0x0,%ax
    256d:	e9 fe 01             	jmp    0x276e
    2570:	ff 76 f0             	push   -0x10(%bp)
    2573:	8b 46 06             	mov    0x6(%bp),%ax
    2576:	8b 56 08             	mov    0x8(%bp),%dx
    2579:	05 d0 01             	add    $0x1d0,%ax
    257c:	52                   	push   %dx
    257d:	50                   	push   %ax
    257e:	c4 5e 06             	les    0x6(%bp),%bx
    2581:	26 ff 77 1e          	push   %es:0x1e(%bx)
    2585:	26 ff 77 1c          	push   %es:0x1c(%bx)
    2589:	e8 a0 dc             	call   0x22c
    258c:	83 c4 0a             	add    $0xa,%sp
    258f:	c4 5e 06             	les    0x6(%bp),%bx
    2592:	26 8b 47 26          	mov    %es:0x26(%bx),%ax
    2596:	26 0b 47 24          	or     %es:0x24(%bx),%ax
    259a:	75 03                	jne    0x259f
    259c:	e9 82 00             	jmp    0x2621
    259f:	c4 5e 06             	les    0x6(%bp),%bx
    25a2:	26 8b 47 2a          	mov    %es:0x2a(%bx),%ax
    25a6:	26 0b 47 28          	or     %es:0x28(%bx),%ax
    25aa:	75 03                	jne    0x25af
    25ac:	e9 72 00             	jmp    0x2621
    25af:	8b 46 ec             	mov    -0x14(%bp),%ax
    25b2:	2b 46 ee             	sub    -0x12(%bp),%ax
    25b5:	89 46 f0             	mov    %ax,-0x10(%bp)
    25b8:	2b d2                	sub    %dx,%dx
    25ba:	c4 5e 06             	les    0x6(%bp),%bx
    25bd:	26 3b 57 2a          	cmp    %es:0x2a(%bx),%dx
    25c1:	73 03                	jae    0x25c6
    25c3:	e9 19 00             	jmp    0x25df
    25c6:	76 03                	jbe    0x25cb
    25c8:	e9 09 00             	jmp    0x25d4
    25cb:	26 3b 47 28          	cmp    %es:0x28(%bx),%ax
    25cf:	73 03                	jae    0x25d4
    25d1:	e9 0b 00             	jmp    0x25df
    25d4:	c4 5e 06             	les    0x6(%bp),%bx
    25d7:	26 8b 47 28          	mov    %es:0x28(%bx),%ax
    25db:	48                   	dec    %ax
    25dc:	89 46 f0             	mov    %ax,-0x10(%bp)
    25df:	c7 46 f6 00 00       	movw   $0x0,-0xa(%bp)
    25e4:	e9 03 00             	jmp    0x25ea
    25e7:	ff 46 f6             	incw   -0xa(%bp)
    25ea:	8b 46 f6             	mov    -0xa(%bp),%ax
    25ed:	39 46 f0             	cmp    %ax,-0x10(%bp)
    25f0:	77 03                	ja     0x25f5
    25f2:	e9 1e 00             	jmp    0x2613
    25f5:	c4 5e 06             	les    0x6(%bp),%bx
    25f8:	03 5e ee             	add    -0x12(%bp),%bx
    25fb:	8b 76 f6             	mov    -0xa(%bp),%si
    25fe:	26 8a 80 d0 01       	mov    %es:0x1d0(%bx,%si),%al
    2603:	c4 5e 06             	les    0x6(%bp),%bx
    2606:	26 c4 5f 24          	les    %es:0x24(%bx),%bx
    260a:	8b 76 f6             	mov    -0xa(%bp),%si
    260d:	26 88 00             	mov    %al,%es:(%bx,%si)
    2610:	e9 d4 ff             	jmp    0x25e7
    2613:	c4 5e 06             	les    0x6(%bp),%bx
    2616:	26 c4 5f 24          	les    %es:0x24(%bx),%bx
    261a:	8b 76 f0             	mov    -0x10(%bp),%si
    261d:	26 c6 00 00          	movb   $0x0,%es:(%bx,%si)
    2621:	8b 46 ee             	mov    -0x12(%bp),%ax
    2624:	c4 5e 06             	les    0x6(%bp),%bx
    2627:	26 c4 1f             	les    %es:(%bx),%bx
    262a:	26 89 47 34          	mov    %ax,%es:0x34(%bx)
    262e:	83 7e f4 00          	cmpw   $0x0,-0xc(%bp)
    2632:	75 03                	jne    0x2637
    2634:	e9 06 00             	jmp    0x263d
    2637:	b8 00 00             	mov    $0x0,%ax
    263a:	e9 13 00             	jmp    0x2650
    263d:	83 7e f8 00          	cmpw   $0x0,-0x8(%bp)
    2641:	75 03                	jne    0x2646
    2643:	e9 07 00             	jmp    0x264d
    2646:	8b 46 f8             	mov    -0x8(%bp),%ax
    2649:	40                   	inc    %ax
    264a:	e9 03 00             	jmp    0x2650
    264d:	8b 46 ec             	mov    -0x14(%bp),%ax
    2650:	c4 5e 06             	les    0x6(%bp),%bx
    2653:	26 c4 1f             	les    %es:(%bx),%bx
    2656:	26 89 47 36          	mov    %ax,%es:0x36(%bx)
    265a:	c4 5e 06             	les    0x6(%bp),%bx
    265d:	26 8b 87 96 09       	mov    %es:0x996(%bx),%ax
    2662:	99                   	cwtd
    2663:	05 01 00             	add    $0x1,%ax
    2666:	83 d2 00             	adc    $0x0,%dx
    2669:	c4 5e 06             	les    0x6(%bp),%bx
    266c:	26 c4 1f             	les    %es:(%bx),%bx
    266f:	26 89 47 14          	mov    %ax,%es:0x14(%bx)
    2673:	26 89 57 16          	mov    %dx,%es:0x16(%bx)
    2677:	81 66 fc fe fb       	andw   $0xfbfe,-0x4(%bp)
    267c:	83 66 fe ff          	andw   $0xffff,-0x2(%bp)
    2680:	ff 76 04             	push   0x4(%bp)
    2683:	b8 68 00             	mov    $0x68,%ax
    2686:	50                   	push   %ax
    2687:	b8 00 04             	mov    $0x400,%ax
    268a:	50                   	push   %ax
    268b:	b8 00 00             	mov    $0x0,%ax
    268e:	50                   	push   %ax
    268f:	2b c0                	sub    %ax,%ax
    2691:	50                   	push   %ax
    2692:	50                   	push   %ax
    2693:	9a d3 28 00 00       	lcall  $0x0,$0x28d3
    2698:	0b d0                	or     %ax,%dx
    269a:	75 03                	jne    0x269f
    269c:	e9 08 00             	jmp    0x26a7
    269f:	83 4e fc 01          	orw    $0x1,-0x4(%bp)
    26a3:	83 4e fe 00          	orw    $0x0,-0x2(%bp)
    26a7:	c4 5e 06             	les    0x6(%bp),%bx
    26aa:	26 80 bf 10 03 00    	cmpb   $0x0,%es:0x310(%bx)
    26b0:	75 03                	jne    0x26b5
    26b2:	e9 83 00             	jmp    0x2738
    26b5:	83 7e f8 00          	cmpw   $0x0,-0x8(%bp)
    26b9:	75 03                	jne    0x26be
    26bb:	e9 7a 00             	jmp    0x2738
    26be:	c4 5e 06             	les    0x6(%bp),%bx
    26c1:	8b 76 f8             	mov    -0x8(%bp),%si
    26c4:	26 80 b8 d1 01 00    	cmpb   $0x0,%es:0x1d1(%bx,%si)
    26ca:	75 03                	jne    0x26cf
    26cc:	e9 69 00             	jmp    0x2738
    26cf:	c7 46 f6 00 00       	movw   $0x0,-0xa(%bp)
    26d4:	e9 03 00             	jmp    0x26da
    26d7:	ff 46 f6             	incw   -0xa(%bp)
    26da:	83 7e f6 04          	cmpw   $0x4,-0xa(%bp)
    26de:	72 03                	jb     0x26e3
    26e0:	e9 55 00             	jmp    0x2738
    26e3:	c4 5e 06             	les    0x6(%bp),%bx
    26e6:	03 5e f8             	add    -0x8(%bp),%bx
    26e9:	8b 76 f6             	mov    -0xa(%bp),%si
    26ec:	26 8a 80 d1 01       	mov    %es:0x1d1(%bx,%si),%al
    26f1:	88 46 ea             	mov    %al,-0x16(%bp)
    26f4:	8a 46 ea             	mov    -0x16(%bp),%al
    26f7:	50                   	push   %ax
    26f8:	e8 91 db             	call   0x28c
    26fb:	83 c4 02             	add    $0x2,%sp
    26fe:	c4 5e 06             	les    0x6(%bp),%bx
    2701:	81 c3 10 03          	add    $0x310,%bx
    2705:	8b 76 f6             	mov    -0xa(%bp),%si
    2708:	26 8a 08             	mov    %es:(%bx,%si),%cl
    270b:	51                   	push   %cx
    270c:	89 46 e8             	mov    %ax,-0x18(%bp)
    270f:	e8 7a db             	call   0x28c
    2712:	83 c4 02             	add    $0x2,%sp
    2715:	3a 46 e8             	cmp    -0x18(%bp),%al
    2718:	75 03                	jne    0x271d
    271a:	e9 0c 00             	jmp    0x2729
    271d:	81 4e fc 00 04       	orw    $0x400,-0x4(%bp)
    2722:	83 4e fe 00          	orw    $0x0,-0x2(%bp)
    2726:	e9 0f 00             	jmp    0x2738
    2729:	80 7e ea 00          	cmpb   $0x0,-0x16(%bp)
    272d:	74 03                	je     0x2732
    272f:	e9 03 00             	jmp    0x2735
    2732:	e9 03 00             	jmp    0x2738
    2735:	e9 9f ff             	jmp    0x26d7
    2738:	8b 46 fc             	mov    -0x4(%bp),%ax
    273b:	8b 56 fe             	mov    -0x2(%bp),%dx
    273e:	c4 5e 06             	les    0x6(%bp),%bx
    2741:	26 c4 1f             	les    %es:(%bx),%bx
    2744:	26 89 47 30          	mov    %ax,%es:0x30(%bx)
    2748:	26 89 57 32          	mov    %dx,%es:0x32(%bx)
    274c:	2b c0                	sub    %ax,%ax
    274e:	50                   	push   %ax
    274f:	50                   	push   %ax
    2750:	ff 76 08             	push   0x8(%bp)
    2753:	ff 76 06             	push   0x6(%bp)
    2756:	e8 46 e2             	call   0x99f
    2759:	83 c4 08             	add    $0x8,%sp
    275c:	ff 76 04             	push   0x4(%bp)
    275f:	b8 01 00             	mov    $0x1,%ax
    2762:	50                   	push   %ax
    2763:	9a fd 27 00 00       	lcall  $0x0,$0x27fd
    2768:	b8 01 00             	mov    $0x1,%ax
    276b:	e9 00 00             	jmp    0x276e
    276e:	5e                   	pop    %si
    276f:	5f                   	pop    %di
    2770:	8b e5                	mov    %bp,%sp
    2772:	5d                   	pop    %bp
    2773:	c3                   	ret
    2774:	1e                   	push   %ds
    2775:	58                   	pop    %ax
    2776:	90                   	nop
    2777:	45                   	inc    %bp
    2778:	55                   	push   %bp
    2779:	8b ec                	mov    %sp,%bp
    277b:	1e                   	push   %ds
    277c:	8e d8                	mov    %ax,%ds
    277e:	81 ec 0e 00          	sub    $0xe,%sp
    2782:	57                   	push   %di
    2783:	56                   	push   %si
    2784:	81 7e 0c 10 01       	cmpw   $0x110,0xc(%bp)
    2789:	74 03                	je     0x278e
    278b:	e9 7c 00             	jmp    0x280a
    278e:	e8 1d d9             	call   0xae
    2791:	89 46 f8             	mov    %ax,-0x8(%bp)
    2794:	3d 00 00             	cmp    $0x0,%ax
    2797:	7c 03                	jl     0x279c
    2799:	e9 06 00             	jmp    0x27a2
    279c:	b8 00 00             	mov    $0x0,%ax
    279f:	e9 68 03             	jmp    0x2b0a
    27a2:	8b 5e f8             	mov    -0x8(%bp),%bx
    27a5:	8b c3                	mov    %bx,%ax
    27a7:	d1 e3                	shl    $1,%bx
    27a9:	d1 e3                	shl    $1,%bx
    27ab:	03 d8                	add    %ax,%bx
    27ad:	d1 e3                	shl    $1,%bx
    27af:	8b 87 26 02          	mov    0x226(%bx),%ax
    27b3:	89 46 f6             	mov    %ax,-0xa(%bp)
    27b6:	3d 00 00             	cmp    $0x0,%ax
    27b9:	74 03                	je     0x27be
    27bb:	e9 06 00             	jmp    0x27c4
    27be:	b8 00 00             	mov    $0x0,%ax
    27c1:	e9 46 03             	jmp    0x2b0a
    27c4:	ff 76 0e             	push   0xe(%bp)
    27c7:	b8 10 00             	mov    $0x10,%ax
    27ca:	1e                   	push   %ds
    27cb:	50                   	push   %ax
    27cc:	ff 76 f6             	push   -0xa(%bp)
    27cf:	9a 9b 14 00 00       	lcall  $0x0,$0x149b
    27d4:	3d 00 00             	cmp    $0x0,%ax
    27d7:	74 03                	je     0x27dc
    27d9:	e9 2b 00             	jmp    0x2807
    27dc:	8b 5e f8             	mov    -0x8(%bp),%bx
    27df:	8b c3                	mov    %bx,%ax
    27e1:	d1 e3                	shl    $1,%bx
    27e3:	d1 e3                	shl    $1,%bx
    27e5:	03 d8                	add    %ax,%bx
    27e7:	d1 e3                	shl    $1,%bx
    27e9:	c7 87 22 02 09 00    	movw   $0x9,0x222(%bx)
    27ef:	c7 87 24 02 00 00    	movw   $0x0,0x224(%bx)
    27f5:	ff 76 0e             	push   0xe(%bp)
    27f8:	b8 00 00             	mov    $0x0,%ax
    27fb:	50                   	push   %ax
    27fc:	9a 90 28 00 00       	lcall  $0x0,$0x2890
    2801:	b8 01 00             	mov    $0x1,%ax
    2804:	e9 03 03             	jmp    0x2b0a
    2807:	e9 10 00             	jmp    0x281a
    280a:	ff 76 0e             	push   0xe(%bp)
    280d:	b8 10 00             	mov    $0x10,%ax
    2810:	1e                   	push   %ds
    2811:	50                   	push   %ax
    2812:	9a c5 14 00 00       	lcall  $0x0,$0x14c5
    2817:	89 46 f6             	mov    %ax,-0xa(%bp)
    281a:	83 7e f6 00          	cmpw   $0x0,-0xa(%bp)
    281e:	74 03                	je     0x2823
    2820:	e9 06 00             	jmp    0x2829
    2823:	b8 00 00             	mov    $0x0,%ax
    2826:	e9 e1 02             	jmp    0x2b0a
    2829:	ff 76 f6             	push   -0xa(%bp)
    282c:	9a 0f 19 00 00       	lcall  $0x0,$0x190f
    2831:	89 46 fa             	mov    %ax,-0x6(%bp)
    2834:	89 56 fc             	mov    %dx,-0x4(%bp)
    2837:	0b d0                	or     %ax,%dx
    2839:	74 03                	je     0x283e
    283b:	e9 06 00             	jmp    0x2844
    283e:	b8 00 00             	mov    $0x0,%ax
    2841:	e9 c6 02             	jmp    0x2b0a
    2844:	8b 46 0c             	mov    0xc(%bp),%ax
    2847:	e9 92 02             	jmp    0x2adc
    284a:	ff 76 0e             	push   0xe(%bp)
    284d:	8b 46 fa             	mov    -0x6(%bp),%ax
    2850:	8b 56 fc             	mov    -0x4(%bp),%dx
    2853:	05 d0 02             	add    $0x2d0,%ax
    2856:	52                   	push   %dx
    2857:	50                   	push   %ax
    2858:	9a fb 15 00 00       	lcall  $0x0,$0x15fb
    285d:	ff 76 fc             	push   -0x4(%bp)
    2860:	ff 76 fa             	push   -0x6(%bp)
    2863:	ff 76 0e             	push   0xe(%bp)
    2866:	e8 72 e6             	call   0xedb
    2869:	83 c4 06             	add    $0x6,%sp
    286c:	3d 00 00             	cmp    $0x0,%ax
    286f:	74 03                	je     0x2874
    2871:	e9 23 00             	jmp    0x2897
    2874:	b8 02 00             	mov    $0x2,%ax
    2877:	ba 00 00             	mov    $0x0,%dx
    287a:	52                   	push   %dx
    287b:	50                   	push   %ax
    287c:	ff 76 fc             	push   -0x4(%bp)
    287f:	ff 76 fa             	push   -0x6(%bp)
    2882:	e8 1a e1             	call   0x99f
    2885:	83 c4 08             	add    $0x8,%sp
    2888:	ff 76 0e             	push   0xe(%bp)
    288b:	b8 00 00             	mov    $0x0,%ax
    288e:	50                   	push   %ax
    288f:	9a ba 24 00 00       	lcall  $0x0,$0x24ba
    2894:	e9 65 02             	jmp    0x2afc
    2897:	c7 46 f4 00 00       	movw   $0x0,-0xc(%bp)
    289c:	e9 03 00             	jmp    0x28a2
    289f:	ff 46 f4             	incw   -0xc(%bp)
    28a2:	8b 46 f4             	mov    -0xc(%bp),%ax
    28a5:	c4 5e fa             	les    -0x6(%bp),%bx
    28a8:	26 39 87 94 09       	cmp    %ax,%es:0x994(%bx)
    28ad:	7f 03                	jg     0x28b2
    28af:	e9 28 00             	jmp    0x28da
    28b2:	ff 76 0e             	push   0xe(%bp)
    28b5:	b8 66 00             	mov    $0x66,%ax
    28b8:	50                   	push   %ax
    28b9:	b8 03 04             	mov    $0x403,%ax
    28bc:	50                   	push   %ax
    28bd:	b8 00 00             	mov    $0x0,%ax
    28c0:	50                   	push   %ax
    28c1:	b8 28 00             	mov    $0x28,%ax
    28c4:	f7 6e f4             	imulw  -0xc(%bp)
    28c7:	03 46 fa             	add    -0x6(%bp),%ax
    28ca:	8b 56 fc             	mov    -0x4(%bp),%dx
    28cd:	05 14 07             	add    $0x714,%ax
    28d0:	52                   	push   %dx
    28d1:	50                   	push   %ax
    28d2:	9a f2 28 00 00       	lcall  $0x0,$0x28f2
    28d7:	e9 c5 ff             	jmp    0x289f
    28da:	ff 76 0e             	push   0xe(%bp)
    28dd:	b8 66 00             	mov    $0x66,%ax
    28e0:	50                   	push   %ax
    28e1:	b8 0e 04             	mov    $0x40e,%ax
    28e4:	50                   	push   %ax
    28e5:	c4 5e fa             	les    -0x6(%bp),%bx
    28e8:	26 ff b7 96 09       	push   %es:0x996(%bx)
    28ed:	2b c0                	sub    %ax,%ax
    28ef:	50                   	push   %ax
    28f0:	50                   	push   %ax
    28f1:	9a 2a 29 00 00       	lcall  $0x0,$0x292a
    28f6:	ff 76 fc             	push   -0x4(%bp)
    28f9:	ff 76 fa             	push   -0x6(%bp)
    28fc:	ff 76 0e             	push   0xe(%bp)
    28ff:	e8 db e9             	call   0x12dd
    2902:	83 c4 06             	add    $0x6,%sp
    2905:	c4 5e fa             	les    -0x6(%bp),%bx
    2908:	26 80 7f 50 00       	cmpb   $0x0,%es:0x50(%bx)
    290d:	75 03                	jne    0x2912
    290f:	e9 1c 00             	jmp    0x292e
    2912:	ff 76 0e             	push   0xe(%bp)
    2915:	b8 64 00             	mov    $0x64,%ax
    2918:	50                   	push   %ax
    2919:	b8 01 04             	mov    $0x401,%ax
    291c:	50                   	push   %ax
    291d:	b8 00 00             	mov    $0x0,%ax
    2920:	50                   	push   %ax
    2921:	b8 00 00             	mov    $0x0,%ax
    2924:	ba ff 7f             	mov    $0x7fff,%dx
    2927:	52                   	push   %dx
    2928:	50                   	push   %ax
    2929:	9a c8 13 00 00       	lcall  $0x0,$0x13c8
    292e:	ff 76 f6             	push   -0xa(%bp)
    2931:	9a f7 1a 00 00       	lcall  $0x0,$0x1af7
    2936:	b8 01 00             	mov    $0x1,%ax
    2939:	e9 ce 01             	jmp    0x2b0a
    293c:	83 7e 0a 02          	cmpw   $0x2,0xa(%bp)
    2940:	74 03                	je     0x2945
    2942:	e9 1f 00             	jmp    0x2964
    2945:	2b c0                	sub    %ax,%ax
    2947:	50                   	push   %ax
    2948:	50                   	push   %ax
    2949:	ff 76 fc             	push   -0x4(%bp)
    294c:	ff 76 fa             	push   -0x6(%bp)
    294f:	e8 4d e0             	call   0x99f
    2952:	83 c4 08             	add    $0x8,%sp
    2955:	ff 76 0e             	push   0xe(%bp)
    2958:	b8 00 00             	mov    $0x0,%ax
    295b:	50                   	push   %ax
    295c:	9a b4 2a 00 00       	lcall  $0x0,$0x2ab4
    2961:	e9 98 01             	jmp    0x2afc
    2964:	83 7e 0a 01          	cmpw   $0x1,0xa(%bp)
    2968:	74 03                	je     0x296d
    296a:	e9 12 00             	jmp    0x297f
    296d:	ff 76 fc             	push   -0x4(%bp)
    2970:	ff 76 fa             	push   -0x6(%bp)
    2973:	ff 76 0e             	push   0xe(%bp)
    2976:	e8 9b f3             	call   0x1d14
    2979:	83 c4 06             	add    $0x6,%sp
    297c:	e9 7d 01             	jmp    0x2afc
    297f:	83 7e 0a 66          	cmpw   $0x66,0xa(%bp)
    2983:	74 03                	je     0x2988
    2985:	e9 59 00             	jmp    0x29e1
    2988:	8b 46 08             	mov    0x8(%bp),%ax
    298b:	48                   	dec    %ax
    298c:	74 03                	je     0x2991
    298e:	e9 50 00             	jmp    0x29e1
    2991:	ff 76 0e             	push   0xe(%bp)
    2994:	b8 66 00             	mov    $0x66,%ax
    2997:	50                   	push   %ax
    2998:	b8 07 04             	mov    $0x407,%ax
    299b:	50                   	push   %ax
    299c:	b8 00 00             	mov    $0x0,%ax
    299f:	50                   	push   %ax
    29a0:	2b c0                	sub    %ax,%ax
    29a2:	50                   	push   %ax
    29a3:	50                   	push   %ax
    29a4:	9a 94 26 00 00       	lcall  $0x0,$0x2694
    29a9:	89 46 f4             	mov    %ax,-0xc(%bp)
    29ac:	3d 00 00             	cmp    $0x0,%ax
    29af:	7d 03                	jge    0x29b4
    29b1:	e9 2a 00             	jmp    0x29de
    29b4:	8b 46 f4             	mov    -0xc(%bp),%ax
    29b7:	c4 5e fa             	les    -0x6(%bp),%bx
    29ba:	26 39 87 94 09       	cmp    %ax,%es:0x994(%bx)
    29bf:	7f 03                	jg     0x29c4
    29c1:	e9 1a 00             	jmp    0x29de
    29c4:	8b 46 f4             	mov    -0xc(%bp),%ax
    29c7:	c4 5e fa             	les    -0x6(%bp),%bx
    29ca:	26 89 87 96 09       	mov    %ax,%es:0x996(%bx)
    29cf:	ff 76 fc             	push   -0x4(%bp)
    29d2:	ff 76 fa             	push   -0x6(%bp)
    29d5:	ff 76 0e             	push   0xe(%bp)
    29d8:	e8 02 e9             	call   0x12dd
    29db:	83 c4 06             	add    $0x6,%sp
    29de:	e9 1b 01             	jmp    0x2afc
    29e1:	83 7e 0a 65          	cmpw   $0x65,0xa(%bp)
    29e5:	74 03                	je     0x29ea
    29e7:	e9 af 00             	jmp    0x2a99
    29ea:	8b 46 08             	mov    0x8(%bp),%ax
    29ed:	48                   	dec    %ax
    29ee:	75 03                	jne    0x29f3
    29f0:	e9 09 00             	jmp    0x29fc
    29f3:	83 7e 08 02          	cmpw   $0x2,0x8(%bp)
    29f7:	74 03                	je     0x29fc
    29f9:	e9 9d 00             	jmp    0x2a99
    29fc:	ff 76 0e             	push   0xe(%bp)
    29ff:	8b 46 fa             	mov    -0x6(%bp),%ax
    2a02:	8b 56 fc             	mov    -0x4(%bp),%dx
    2a05:	05 50 01             	add    $0x150,%ax
    2a08:	52                   	push   %dx
    2a09:	50                   	push   %ax
    2a0a:	b8 65 00             	mov    $0x65,%ax
    2a0d:	50                   	push   %ax
    2a0e:	9a ff ff 00 00       	lcall  $0x0,$0xffff
    2a13:	89 46 f2             	mov    %ax,-0xe(%bp)
    2a16:	83 7e f2 00          	cmpw   $0x0,-0xe(%bp)
    2a1a:	75 03                	jne    0x2a1f
    2a1c:	e9 4b 00             	jmp    0x2a6a
    2a1f:	83 7e 08 02          	cmpw   $0x2,0x8(%bp)
    2a23:	74 03                	je     0x2a28
    2a25:	e9 3f 00             	jmp    0x2a67
    2a28:	8b 46 fa             	mov    -0x6(%bp),%ax
    2a2b:	8b 56 fc             	mov    -0x4(%bp),%dx
    2a2e:	05 50 01             	add    $0x150,%ax
    2a31:	52                   	push   %dx
    2a32:	50                   	push   %ax
    2a33:	ff 76 fc             	push   -0x4(%bp)
    2a36:	ff 76 fa             	push   -0x6(%bp)
    2a39:	e8 3a e0             	call   0xa76
    2a3c:	83 c4 08             	add    $0x8,%sp
    2a3f:	3d 00 00             	cmp    $0x0,%ax
    2a42:	75 03                	jne    0x2a47
    2a44:	e9 12 00             	jmp    0x2a59
    2a47:	ff 76 fc             	push   -0x4(%bp)
    2a4a:	ff 76 fa             	push   -0x6(%bp)
    2a4d:	ff 76 0e             	push   0xe(%bp)
    2a50:	e8 8a e8             	call   0x12dd
    2a53:	83 c4 06             	add    $0x6,%sp
    2a56:	e9 0e 00             	jmp    0x2a67
    2a59:	b8 fa 01             	mov    $0x1fa,%ax
    2a5c:	1e                   	push   %ds
    2a5d:	50                   	push   %ax
    2a5e:	ff 76 0e             	push   0xe(%bp)
    2a61:	e8 cb f0             	call   0x1b2f
    2a64:	83 c4 06             	add    $0x6,%sp
    2a67:	e9 2f 00             	jmp    0x2a99
    2a6a:	ff 76 0e             	push   0xe(%bp)
    2a6d:	b8 64 00             	mov    $0x64,%ax
    2a70:	50                   	push   %ax
    2a71:	8b 46 fa             	mov    -0x6(%bp),%ax
    2a74:	8b 56 fc             	mov    -0x4(%bp),%dx
    2a77:	05 50 01             	add    $0x150,%ax
    2a7a:	52                   	push   %dx
    2a7b:	50                   	push   %ax
    2a7c:	9a 45 1e 00 00       	lcall  $0x0,$0x1e45
    2a81:	83 7e 08 02          	cmpw   $0x2,0x8(%bp)
    2a85:	74 03                	je     0x2a8a
    2a87:	e9 0f 00             	jmp    0x2a99
    2a8a:	ff 76 fc             	push   -0x4(%bp)
    2a8d:	ff 76 fa             	push   -0x6(%bp)
    2a90:	ff 76 0e             	push   0xe(%bp)
    2a93:	e8 7e f2             	call   0x1d14
    2a96:	83 c4 06             	add    $0x6,%sp
    2a99:	e9 60 00             	jmp    0x2afc
    2a9c:	2b c0                	sub    %ax,%ax
    2a9e:	50                   	push   %ax
    2a9f:	50                   	push   %ax
    2aa0:	ff 76 fc             	push   -0x4(%bp)
    2aa3:	ff 76 fa             	push   -0x6(%bp)
    2aa6:	e8 f6 de             	call   0x99f
    2aa9:	83 c4 08             	add    $0x8,%sp
    2aac:	ff 76 0e             	push   0xe(%bp)
    2aaf:	b8 00 00             	mov    $0x0,%ax
    2ab2:	50                   	push   %ax
    2ab3:	9a 64 27 00 00       	lcall  $0x0,$0x2764
    2ab8:	e9 41 00             	jmp    0x2afc
    2abb:	ff 76 0e             	push   0xe(%bp)
    2abe:	b8 10 00             	mov    $0x10,%ax
    2ac1:	1e                   	push   %ds
    2ac2:	50                   	push   %ax
    2ac3:	9a 18 18 00 00       	lcall  $0x0,$0x1818
    2ac8:	e9 31 00             	jmp    0x2afc
    2acb:	ff 76 f6             	push   -0xa(%bp)
    2ace:	9a 00 2b 00 00       	lcall  $0x0,$0x2b00
    2ad3:	b8 00 00             	mov    $0x0,%ax
    2ad6:	e9 31 00             	jmp    0x2b0a
    2ad9:	e9 20 00             	jmp    0x2afc
    2adc:	48                   	dec    %ax
    2add:	48                   	dec    %ax
    2ade:	75 03                	jne    0x2ae3
    2ae0:	e9 d8 ff             	jmp    0x2abb
    2ae3:	2d 0e 00             	sub    $0xe,%ax
    2ae6:	75 03                	jne    0x2aeb
    2ae8:	e9 b1 ff             	jmp    0x2a9c
    2aeb:	2d 00 01             	sub    $0x100,%ax
    2aee:	75 03                	jne    0x2af3
    2af0:	e9 57 fd             	jmp    0x284a
    2af3:	48                   	dec    %ax
    2af4:	75 03                	jne    0x2af9
    2af6:	e9 43 fe             	jmp    0x293c
    2af9:	e9 cf ff             	jmp    0x2acb
    2afc:	ff 76 f6             	push   -0xa(%bp)
    2aff:	9a 32 29 00 00       	lcall  $0x0,$0x2932
    2b04:	b8 01 00             	mov    $0x1,%ax
    2b07:	e9 00 00             	jmp    0x2b0a
    2b0a:	5e                   	pop    %si
    2b0b:	5f                   	pop    %di
    2b0c:	83 ed 02             	sub    $0x2,%bp
    2b0f:	8b e5                	mov    %bp,%sp
    2b11:	1f                   	pop    %ds
    2b12:	5d                   	pop    %bp
    2b13:	4d                   	dec    %bp
    2b14:	ca 0a 00             	lret   $0xa
    2b17:	55                   	push   %bp
    2b18:	8b ec                	mov    %sp,%bp
    2b1a:	81 ec 18 00          	sub    $0x18,%sp
    2b1e:	57                   	push   %di
    2b1f:	56                   	push   %si
    2b20:	e8 8b d5             	call   0xae
    2b23:	89 46 f0             	mov    %ax,-0x10(%bp)
    2b26:	c7 46 e8 00 00       	movw   $0x0,-0x18(%bp)
    2b2b:	83 7e f0 00          	cmpw   $0x0,-0x10(%bp)
    2b2f:	7c 03                	jl     0x2b34
    2b31:	e9 06 00             	jmp    0x2b3a
    2b34:	b8 00 00             	mov    $0x0,%ax
    2b37:	e9 86 08             	jmp    0x33c0
    2b3a:	8b 5e f0             	mov    -0x10(%bp),%bx
    2b3d:	8b c3                	mov    %bx,%ax
    2b3f:	d1 e3                	shl    $1,%bx
    2b41:	d1 e3                	shl    $1,%bx
    2b43:	03 d8                	add    %ax,%bx
    2b45:	d1 e3                	shl    $1,%bx
    2b47:	2b c0                	sub    %ax,%ax
    2b49:	89 87 24 02          	mov    %ax,0x224(%bx)
    2b4d:	89 87 22 02          	mov    %ax,0x222(%bx)
    2b51:	8b 46 06             	mov    0x6(%bp),%ax
    2b54:	0b 46 04             	or     0x4(%bp),%ax
    2b57:	75 03                	jne    0x2b5c
    2b59:	e9 2e 00             	jmp    0x2b8a
    2b5c:	b8 48 00             	mov    $0x48,%ax
    2b5f:	50                   	push   %ax
    2b60:	ff 76 06             	push   0x6(%bp)
    2b63:	ff 76 04             	push   0x4(%bp)
    2b66:	e8 0a d6             	call   0x173
    2b69:	83 c4 06             	add    $0x6,%sp
    2b6c:	3d 00 00             	cmp    $0x0,%ax
    2b6f:	75 03                	jne    0x2b74
    2b71:	e9 16 00             	jmp    0x2b8a
    2b74:	c4 5e 04             	les    0x4(%bp),%bx
    2b77:	26 83 3f 48          	cmpw   $0x48,%es:(%bx)
    2b7b:	74 03                	je     0x2b80
    2b7d:	e9 0a 00             	jmp    0x2b8a
    2b80:	26 83 7f 02 00       	cmpw   $0x0,%es:0x2(%bx)
    2b85:	75 03                	jne    0x2b8a
    2b87:	e9 1f 00             	jmp    0x2ba9
    2b8a:	8b 5e f0             	mov    -0x10(%bp),%bx
    2b8d:	8b c3                	mov    %bx,%ax
    2b8f:	d1 e3                	shl    $1,%bx
    2b91:	d1 e3                	shl    $1,%bx
    2b93:	03 d8                	add    %ax,%bx
    2b95:	d1 e3                	shl    $1,%bx
    2b97:	c7 87 22 02 01 00    	movw   $0x1,0x222(%bx)
    2b9d:	c7 87 24 02 00 00    	movw   $0x0,0x224(%bx)
    2ba3:	b8 00 00             	mov    $0x0,%ax
    2ba6:	e9 17 08             	jmp    0x33c0
    2ba9:	8b 5e f0             	mov    -0x10(%bp),%bx
    2bac:	8b c3                	mov    %bx,%ax
    2bae:	d1 e3                	shl    $1,%bx
    2bb0:	d1 e3                	shl    $1,%bx
    2bb2:	03 d8                	add    %ax,%bx
    2bb4:	d1 e3                	shl    $1,%bx
    2bb6:	83 bf 26 02 00       	cmpw   $0x0,0x226(%bx)
    2bbb:	74 03                	je     0x2bc0
    2bbd:	e9 28 00             	jmp    0x2be8
    2bc0:	c4 5e 04             	les    0x4(%bp),%bx
    2bc3:	26 8b 47 30          	mov    %es:0x30(%bx),%ax
    2bc7:	26 8b 57 32          	mov    %es:0x32(%bx),%dx
    2bcb:	25 f0 43             	and    $0x43f0,%ax
    2bce:	83 e2 ff             	and    $0xffff,%dx
    2bd1:	0b d0                	or     %ax,%dx
    2bd3:	74 03                	je     0x2bd8
    2bd5:	e9 10 00             	jmp    0x2be8
    2bd8:	c4 5e 04             	les    0x4(%bp),%bx
    2bdb:	26 8b 47 0e          	mov    %es:0xe(%bx),%ax
    2bdf:	26 0b 47 0c          	or     %es:0xc(%bx),%ax
    2be3:	75 03                	jne    0x2be8
    2be5:	e9 1f 00             	jmp    0x2c07
    2be8:	8b 5e f0             	mov    -0x10(%bp),%bx
    2beb:	8b c3                	mov    %bx,%ax
    2bed:	d1 e3                	shl    $1,%bx
    2bef:	d1 e3                	shl    $1,%bx
    2bf1:	03 d8                	add    %ax,%bx
    2bf3:	d1 e3                	shl    $1,%bx
    2bf5:	c7 87 22 02 02 00    	movw   $0x2,0x222(%bx)
    2bfb:	c7 87 24 02 00 00    	movw   $0x0,0x224(%bx)
    2c01:	b8 00 00             	mov    $0x0,%ax
    2c04:	e9 b9 07             	jmp    0x33c0
    2c07:	c4 5e 04             	les    0x4(%bp),%bx
    2c0a:	26 8b 47 1a          	mov    %es:0x1a(%bx),%ax
    2c0e:	26 0b 47 18          	or     %es:0x18(%bx),%ax
    2c12:	75 03                	jne    0x2c17
    2c14:	e9 47 00             	jmp    0x2c5e
    2c17:	c4 5e 04             	les    0x4(%bp),%bx
    2c1a:	26 8b 47 1e          	mov    %es:0x1e(%bx),%ax
    2c1e:	26 0b 47 1c          	or     %es:0x1c(%bx),%ax
    2c22:	75 03                	jne    0x2c27
    2c24:	e9 37 00             	jmp    0x2c5e
    2c27:	c4 5e 04             	les    0x4(%bp),%bx
    2c2a:	26 83 7f 1e 00       	cmpw   $0x0,%es:0x1e(%bx)
    2c2f:	76 03                	jbe    0x2c34
    2c31:	e9 2a 00             	jmp    0x2c5e
    2c34:	26 83 7f 1c ff       	cmpw   $0xffff,%es:0x1c(%bx)
    2c39:	76 03                	jbe    0x2c3e
    2c3b:	e9 20 00             	jmp    0x2c5e
    2c3e:	c4 5e 04             	les    0x4(%bp),%bx
    2c41:	26 ff 77 1c          	push   %es:0x1c(%bx)
    2c45:	c4 5e 04             	les    0x4(%bp),%bx
    2c48:	26 ff 77 1a          	push   %es:0x1a(%bx)
    2c4c:	26 ff 77 18          	push   %es:0x18(%bx)
    2c50:	e8 20 d5             	call   0x173
    2c53:	83 c4 06             	add    $0x6,%sp
    2c56:	3d 00 00             	cmp    $0x0,%ax
    2c59:	74 03                	je     0x2c5e
    2c5b:	e9 1f 00             	jmp    0x2c7d
    2c5e:	8b 5e f0             	mov    -0x10(%bp),%bx
    2c61:	8b c3                	mov    %bx,%ax
    2c63:	d1 e3                	shl    $1,%bx
    2c65:	d1 e3                	shl    $1,%bx
    2c67:	03 d8                	add    %ax,%bx
    2c69:	d1 e3                	shl    $1,%bx
    2c6b:	c7 87 22 02 02 30    	movw   $0x3002,0x222(%bx)
    2c71:	c7 87 24 02 00 00    	movw   $0x0,0x224(%bx)
    2c77:	b8 00 00             	mov    $0x0,%ax
    2c7a:	e9 43 07             	jmp    0x33c0
    2c7d:	c4 5e 04             	les    0x4(%bp),%bx
    2c80:	26 8b 47 22          	mov    %es:0x22(%bx),%ax
    2c84:	26 0b 47 20          	or     %es:0x20(%bx),%ax
    2c88:	75 03                	jne    0x2c8d
    2c8a:	e9 56 00             	jmp    0x2ce3
    2c8d:	c4 5e 04             	les    0x4(%bp),%bx
    2c90:	26 83 7f 26 00       	cmpw   $0x0,%es:0x26(%bx)
    2c95:	76 03                	jbe    0x2c9a
    2c97:	e9 2a 00             	jmp    0x2cc4
    2c9a:	26 83 7f 24 ff       	cmpw   $0xffff,%es:0x24(%bx)
    2c9f:	76 03                	jbe    0x2ca4
    2ca1:	e9 20 00             	jmp    0x2cc4
    2ca4:	c4 5e 04             	les    0x4(%bp),%bx
    2ca7:	26 ff 77 24          	push   %es:0x24(%bx)
    2cab:	c4 5e 04             	les    0x4(%bp),%bx
    2cae:	26 ff 77 22          	push   %es:0x22(%bx)
    2cb2:	26 ff 77 20          	push   %es:0x20(%bx)
    2cb6:	e8 ba d4             	call   0x173
    2cb9:	83 c4 06             	add    $0x6,%sp
    2cbc:	3d 00 00             	cmp    $0x0,%ax
    2cbf:	74 03                	je     0x2cc4
    2cc1:	e9 1f 00             	jmp    0x2ce3
    2cc4:	8b 5e f0             	mov    -0x10(%bp),%bx
    2cc7:	8b c3                	mov    %bx,%ax
    2cc9:	d1 e3                	shl    $1,%bx
    2ccb:	d1 e3                	shl    $1,%bx
    2ccd:	03 d8                	add    %ax,%bx
    2ccf:	d1 e3                	shl    $1,%bx
    2cd1:	c7 87 22 02 02 30    	movw   $0x3002,0x222(%bx)
    2cd7:	c7 87 24 02 00 00    	movw   $0x0,0x224(%bx)
    2cdd:	b8 00 00             	mov    $0x0,%ax
    2ce0:	e9 dd 06             	jmp    0x33c0
    2ce3:	b8 40 00             	mov    $0x40,%ax
    2ce6:	50                   	push   %ax
    2ce7:	b8 28 11             	mov    $0x1128,%ax
    2cea:	ba 00 00             	mov    $0x0,%dx
    2ced:	52                   	push   %dx
    2cee:	50                   	push   %ax
    2cef:	9a e5 18 00 00       	lcall  $0x0,$0x18e5
    2cf4:	89 46 ee             	mov    %ax,-0x12(%bp)
    2cf7:	3d 00 00             	cmp    $0x0,%ax
    2cfa:	74 03                	je     0x2cff
    2cfc:	e9 1f 00             	jmp    0x2d1e
    2cff:	8b 5e f0             	mov    -0x10(%bp),%bx
    2d02:	8b c3                	mov    %bx,%ax
    2d04:	d1 e3                	shl    $1,%bx
    2d06:	d1 e3                	shl    $1,%bx
    2d08:	03 d8                	add    %ax,%bx
    2d0a:	d1 e3                	shl    $1,%bx
    2d0c:	c7 87 22 02 09 00    	movw   $0x9,0x222(%bx)
    2d12:	c7 87 24 02 00 00    	movw   $0x0,0x224(%bx)
    2d18:	b8 00 00             	mov    $0x0,%ax
    2d1b:	e9 a2 06             	jmp    0x33c0
    2d1e:	ff 76 ee             	push   -0x12(%bp)
    2d21:	9a 2d 28 00 00       	lcall  $0x0,$0x282d
    2d26:	89 46 f8             	mov    %ax,-0x8(%bp)
    2d29:	89 56 fa             	mov    %dx,-0x6(%bp)
    2d2c:	0b d0                	or     %ax,%dx
    2d2e:	74 03                	je     0x2d33
    2d30:	e9 27 00             	jmp    0x2d5a
    2d33:	ff 76 ee             	push   -0x12(%bp)
    2d36:	9a ef 1a 00 00       	lcall  $0x0,$0x1aef
    2d3b:	8b 5e f0             	mov    -0x10(%bp),%bx
    2d3e:	8b c3                	mov    %bx,%ax
    2d40:	d1 e3                	shl    $1,%bx
    2d42:	d1 e3                	shl    $1,%bx
    2d44:	03 d8                	add    %ax,%bx
    2d46:	d1 e3                	shl    $1,%bx
    2d48:	c7 87 22 02 0a 00    	movw   $0xa,0x222(%bx)
    2d4e:	c7 87 24 02 00 00    	movw   $0x0,0x224(%bx)
    2d54:	b8 00 00             	mov    $0x0,%ax
    2d57:	e9 66 06             	jmp    0x33c0
    2d5a:	8b 46 ee             	mov    -0x12(%bp),%ax
    2d5d:	c4 5e f8             	les    -0x8(%bp),%bx
    2d60:	26 89 87 9c 10       	mov    %ax,%es:0x109c(%bx)
    2d65:	c4 5e f8             	les    -0x8(%bp),%bx
    2d68:	26 c7 87 9e 10 ff ff 	movw   $0xffff,%es:0x109e(%bx)
    2d6f:	8b 46 f0             	mov    -0x10(%bp),%ax
    2d72:	c4 5e f8             	les    -0x8(%bp),%bx
    2d75:	26 89 47 4e          	mov    %ax,%es:0x4e(%bx)
    2d79:	8b 46 04             	mov    0x4(%bp),%ax
    2d7c:	8b 56 06             	mov    0x6(%bp),%dx
    2d7f:	c4 5e f8             	les    -0x8(%bp),%bx
    2d82:	26 89 07             	mov    %ax,%es:(%bx)
    2d85:	26 89 57 02          	mov    %dx,%es:0x2(%bx)
    2d89:	8b 46 08             	mov    0x8(%bp),%ax
    2d8c:	c4 5e f8             	les    -0x8(%bp),%bx
    2d8f:	26 89 47 4c          	mov    %ax,%es:0x4c(%bx)
    2d93:	c4 5e f8             	les    -0x8(%bp),%bx
    2d96:	8b 46 04             	mov    0x4(%bp),%ax
    2d99:	8b 56 06             	mov    0x6(%bp),%dx
    2d9c:	1e                   	push   %ds
    2d9d:	8d 7f 04             	lea    0x4(%bx),%di
    2da0:	8b f0                	mov    %ax,%si
    2da2:	8e da                	mov    %dx,%ds
    2da4:	b9 24 00             	mov    $0x24,%cx
    2da7:	f3 a5                	rep movsw %ds:(%si),%es:(%di)
    2da9:	1f                   	pop    %ds
    2daa:	9a fd 0b 00 00       	lcall  $0x0,$0xbfd
    2daf:	c4 5e f8             	les    -0x8(%bp),%bx
    2db2:	26 89 87 98 09       	mov    %ax,%es:0x998(%bx)
    2db7:	c4 5e f8             	les    -0x8(%bp),%bx
    2dba:	26 ff b7 98 09       	push   %es:0x998(%bx)
    2dbf:	ff 76 fa             	push   -0x6(%bp)
    2dc2:	ff 76 f8             	push   -0x8(%bp)
    2dc5:	e8 05 dc             	call   0x9cd
    2dc8:	83 c4 06             	add    $0x6,%sp
    2dcb:	3d 00 00             	cmp    $0x0,%ax
    2dce:	74 03                	je     0x2dd3
    2dd0:	e9 17 00             	jmp    0x2dea
    2dd3:	b8 02 00             	mov    $0x2,%ax
    2dd6:	ba 00 00             	mov    $0x0,%dx
    2dd9:	52                   	push   %dx
    2dda:	50                   	push   %ax
    2ddb:	ff 76 fa             	push   -0x6(%bp)
    2dde:	ff 76 f8             	push   -0x8(%bp)
    2de1:	e8 bb db             	call   0x99f
    2de4:	83 c4 08             	add    $0x8,%sp
    2de7:	e9 3e 05             	jmp    0x3328
    2dea:	c4 5e 04             	les    0x4(%bp),%bx
    2ded:	26 8b 47 1c          	mov    %es:0x1c(%bx),%ax
    2df1:	89 46 ea             	mov    %ax,-0x16(%bp)
    2df4:	3d 80 00             	cmp    $0x80,%ax
    2df7:	77 03                	ja     0x2dfc
    2df9:	e9 05 00             	jmp    0x2e01
    2dfc:	c7 46 ea 80 00       	movw   $0x80,-0x16(%bp)
    2e01:	ff 76 ea             	push   -0x16(%bp)
    2e04:	c4 5e 04             	les    0x4(%bp),%bx
    2e07:	26 ff 77 1a          	push   %es:0x1a(%bx)
    2e0b:	26 ff 77 18          	push   %es:0x18(%bx)
    2e0f:	e8 a7 d3             	call   0x1b9
    2e12:	83 c4 06             	add    $0x6,%sp
    2e15:	3b 46 ea             	cmp    -0x16(%bp),%ax
    2e18:	75 03                	jne    0x2e1d
    2e1a:	e9 28 00             	jmp    0x2e45
    2e1d:	b8 80 00             	mov    $0x80,%ax
    2e20:	50                   	push   %ax
    2e21:	c4 5e 04             	les    0x4(%bp),%bx
    2e24:	26 ff 77 1a          	push   %es:0x1a(%bx)
    2e28:	26 ff 77 18          	push   %es:0x18(%bx)
    2e2c:	8b 46 f8             	mov    -0x8(%bp),%ax
    2e2f:	8b 56 fa             	mov    -0x6(%bp),%dx
    2e32:	05 50 00             	add    $0x50,%ax
    2e35:	52                   	push   %dx
    2e36:	50                   	push   %ax
    2e37:	e8 f2 d3             	call   0x22c
    2e3a:	83 c4 0a             	add    $0xa,%sp
    2e3d:	3d 00 00             	cmp    $0x0,%ax
    2e40:	74 03                	je     0x2e45
    2e42:	e9 17 00             	jmp    0x2e5c
    2e45:	b8 02 30             	mov    $0x3002,%ax
    2e48:	ba 00 00             	mov    $0x0,%dx
    2e4b:	52                   	push   %dx
    2e4c:	50                   	push   %ax
    2e4d:	ff 76 fa             	push   -0x6(%bp)
    2e50:	ff 76 f8             	push   -0x8(%bp)
    2e53:	e8 49 db             	call   0x99f
    2e56:	83 c4 08             	add    $0x8,%sp
    2e59:	e9 cc 04             	jmp    0x3328
    2e5c:	ff 76 fa             	push   -0x6(%bp)
    2e5f:	ff 76 f8             	push   -0x8(%bp)
    2e62:	e8 ba dd             	call   0xc1f
    2e65:	83 c4 04             	add    $0x4,%sp
    2e68:	3d 00 00             	cmp    $0x0,%ax
    2e6b:	74 03                	je     0x2e70
    2e6d:	e9 17 00             	jmp    0x2e87
    2e70:	b8 02 00             	mov    $0x2,%ax
    2e73:	ba 00 00             	mov    $0x0,%dx
    2e76:	52                   	push   %dx
    2e77:	50                   	push   %ax
    2e78:	ff 76 fa             	push   -0x6(%bp)
    2e7b:	ff 76 f8             	push   -0x8(%bp)
    2e7e:	e8 1e db             	call   0x99f
    2e81:	83 c4 08             	add    $0x8,%sp
    2e84:	e9 a1 04             	jmp    0x3328
    2e87:	c4 5e 04             	les    0x4(%bp),%bx
    2e8a:	26 8b 47 2e          	mov    %es:0x2e(%bx),%ax
    2e8e:	26 0b 47 2c          	or     %es:0x2c(%bx),%ax
    2e92:	75 03                	jne    0x2e97
    2e94:	e9 42 00             	jmp    0x2ed9
    2e97:	b8 40 00             	mov    $0x40,%ax
    2e9a:	50                   	push   %ax
    2e9b:	c4 5e 04             	les    0x4(%bp),%bx
    2e9e:	26 ff 77 2e          	push   %es:0x2e(%bx)
    2ea2:	26 ff 77 2c          	push   %es:0x2c(%bx)
    2ea6:	8b 46 f8             	mov    -0x8(%bp),%ax
    2ea9:	8b 56 fa             	mov    -0x6(%bp),%dx
    2eac:	05 d0 02             	add    $0x2d0,%ax
    2eaf:	52                   	push   %dx
    2eb0:	50                   	push   %ax
    2eb1:	e8 78 d3             	call   0x22c
    2eb4:	83 c4 0a             	add    $0xa,%sp
    2eb7:	3d 00 00             	cmp    $0x0,%ax
    2eba:	74 03                	je     0x2ebf
    2ebc:	e9 17 00             	jmp    0x2ed6
    2ebf:	b8 02 00             	mov    $0x2,%ax
    2ec2:	ba 00 00             	mov    $0x0,%dx
    2ec5:	52                   	push   %dx
    2ec6:	50                   	push   %ax
    2ec7:	ff 76 fa             	push   -0x6(%bp)
    2eca:	ff 76 f8             	push   -0x8(%bp)
    2ecd:	e8 cf da             	call   0x99f
    2ed0:	83 c4 08             	add    $0x8,%sp
    2ed3:	e9 52 04             	jmp    0x3328
    2ed6:	e9 29 00             	jmp    0x2f02
    2ed9:	b8 40 00             	mov    $0x40,%ax
    2edc:	50                   	push   %ax
    2edd:	83 7e 08 00          	cmpw   $0x0,0x8(%bp)
    2ee1:	75 03                	jne    0x2ee6
    2ee3:	e9 06 00             	jmp    0x2eec
    2ee6:	b8 09 02             	mov    $0x209,%ax
    2ee9:	e9 03 00             	jmp    0x2eef
    2eec:	b8 13 02             	mov    $0x213,%ax
    2eef:	1e                   	push   %ds
    2ef0:	50                   	push   %ax
    2ef1:	8b 46 f8             	mov    -0x8(%bp),%ax
    2ef4:	8b 56 fa             	mov    -0x6(%bp),%dx
    2ef7:	05 d0 02             	add    $0x2d0,%ax
    2efa:	52                   	push   %dx
    2efb:	50                   	push   %ax
    2efc:	e8 2d d3             	call   0x22c
    2eff:	83 c4 0a             	add    $0xa,%sp
    2f02:	c4 5e 04             	les    0x4(%bp),%bx
    2f05:	26 8b 47 3a          	mov    %es:0x3a(%bx),%ax
    2f09:	26 0b 47 38          	or     %es:0x38(%bx),%ax
    2f0d:	75 03                	jne    0x2f12
    2f0f:	e9 15 01             	jmp    0x3027
    2f12:	b8 04 00             	mov    $0x4,%ax
    2f15:	50                   	push   %ax
    2f16:	c4 5e 04             	les    0x4(%bp),%bx
    2f19:	26 ff 77 3a          	push   %es:0x3a(%bx)
    2f1d:	26 ff 77 38          	push   %es:0x38(%bx)
    2f21:	e8 95 d2             	call   0x1b9
    2f24:	83 c4 06             	add    $0x6,%sp
    2f27:	89 46 ea             	mov    %ax,-0x16(%bp)
    2f2a:	3d 04 00             	cmp    $0x4,%ax
    2f2d:	74 03                	je     0x2f32
    2f2f:	e9 17 00             	jmp    0x2f49
    2f32:	b8 02 30             	mov    $0x3002,%ax
    2f35:	ba 00 00             	mov    $0x0,%dx
    2f38:	52                   	push   %dx
    2f39:	50                   	push   %ax
    2f3a:	ff 76 fa             	push   -0x6(%bp)
    2f3d:	ff 76 f8             	push   -0x8(%bp)
    2f40:	e8 5c da             	call   0x99f
    2f43:	83 c4 08             	add    $0x8,%sp
    2f46:	e9 df 03             	jmp    0x3328
    2f49:	c7 46 ec 00 00       	movw   $0x0,-0x14(%bp)
    2f4e:	e9 03 00             	jmp    0x2f54
    2f51:	ff 46 ec             	incw   -0x14(%bp)
    2f54:	8b 46 ec             	mov    -0x14(%bp),%ax
    2f57:	39 46 ea             	cmp    %ax,-0x16(%bp)
    2f5a:	77 03                	ja     0x2f5f
    2f5c:	e9 a8 00             	jmp    0x3007
    2f5f:	c4 5e 04             	les    0x4(%bp),%bx
    2f62:	26 c4 5f 38          	les    %es:0x38(%bx),%bx
    2f66:	8b 76 ec             	mov    -0x14(%bp),%si
    2f69:	26 8a 00             	mov    %es:(%bx,%si),%al
    2f6c:	50                   	push   %ax
    2f6d:	e8 4b d3             	call   0x2bb
    2f70:	83 c4 02             	add    $0x2,%sp
    2f73:	3d 00 00             	cmp    $0x0,%ax
    2f76:	74 03                	je     0x2f7b
    2f78:	e9 72 00             	jmp    0x2fed
    2f7b:	c4 5e 04             	les    0x4(%bp),%bx
    2f7e:	26 c4 5f 38          	les    %es:0x38(%bx),%bx
    2f82:	8b 76 ec             	mov    -0x14(%bp),%si
    2f85:	26 80 38 2e          	cmpb   $0x2e,%es:(%bx,%si)
    2f89:	75 03                	jne    0x2f8e
    2f8b:	e9 5f 00             	jmp    0x2fed
    2f8e:	c4 5e 04             	les    0x4(%bp),%bx
    2f91:	26 c4 5f 38          	les    %es:0x38(%bx),%bx
    2f95:	8b 76 ec             	mov    -0x14(%bp),%si
    2f98:	26 80 38 2a          	cmpb   $0x2a,%es:(%bx,%si)
    2f9c:	75 03                	jne    0x2fa1
    2f9e:	e9 4c 00             	jmp    0x2fed
    2fa1:	c4 5e 04             	les    0x4(%bp),%bx
    2fa4:	26 c4 5f 38          	les    %es:0x38(%bx),%bx
    2fa8:	8b 76 ec             	mov    -0x14(%bp),%si
    2fab:	26 80 38 3f          	cmpb   $0x3f,%es:(%bx,%si)
    2faf:	75 03                	jne    0x2fb4
    2fb1:	e9 39 00             	jmp    0x2fed
    2fb4:	c4 5e 04             	les    0x4(%bp),%bx
    2fb7:	26 c4 5f 38          	les    %es:0x38(%bx),%bx
    2fbb:	8b 76 ec             	mov    -0x14(%bp),%si
    2fbe:	26 80 38 5c          	cmpb   $0x5c,%es:(%bx,%si)
    2fc2:	75 03                	jne    0x2fc7
    2fc4:	e9 26 00             	jmp    0x2fed
    2fc7:	c4 5e 04             	les    0x4(%bp),%bx
    2fca:	26 c4 5f 38          	les    %es:0x38(%bx),%bx
    2fce:	8b 76 ec             	mov    -0x14(%bp),%si
    2fd1:	26 80 38 2f          	cmpb   $0x2f,%es:(%bx,%si)
    2fd5:	75 03                	jne    0x2fda
    2fd7:	e9 13 00             	jmp    0x2fed
    2fda:	c4 5e 04             	les    0x4(%bp),%bx
    2fdd:	26 c4 5f 38          	les    %es:0x38(%bx),%bx
    2fe1:	8b 76 ec             	mov    -0x14(%bp),%si
    2fe4:	26 80 38 3a          	cmpb   $0x3a,%es:(%bx,%si)
    2fe8:	74 03                	je     0x2fed
    2fea:	e9 17 00             	jmp    0x3004
    2fed:	b8 02 30             	mov    $0x3002,%ax
    2ff0:	ba 00 00             	mov    $0x0,%dx
    2ff3:	52                   	push   %dx
    2ff4:	50                   	push   %ax
    2ff5:	ff 76 fa             	push   -0x6(%bp)
    2ff8:	ff 76 f8             	push   -0x8(%bp)
    2ffb:	e8 a1 d9             	call   0x99f
    2ffe:	83 c4 08             	add    $0x8,%sp
    3001:	e9 24 03             	jmp    0x3328
    3004:	e9 4a ff             	jmp    0x2f51
    3007:	b8 04 00             	mov    $0x4,%ax
    300a:	50                   	push   %ax
    300b:	c4 5e 04             	les    0x4(%bp),%bx
    300e:	26 ff 77 3a          	push   %es:0x3a(%bx)
    3012:	26 ff 77 38          	push   %es:0x38(%bx)
    3016:	8b 46 f8             	mov    -0x8(%bp),%ax
    3019:	8b 56 fa             	mov    -0x6(%bp),%dx
    301c:	05 10 03             	add    $0x310,%ax
    301f:	52                   	push   %dx
    3020:	50                   	push   %ax
    3021:	e8 08 d2             	call   0x22c
    3024:	83 c4 0a             	add    $0xa,%sp
    3027:	c4 5e 04             	les    0x4(%bp),%bx
    302a:	26 8b 47 2a          	mov    %es:0x2a(%bx),%ax
    302e:	26 0b 47 28          	or     %es:0x28(%bx),%ax
    3032:	75 03                	jne    0x3037
    3034:	e9 7a 00             	jmp    0x30b1
    3037:	b8 80 00             	mov    $0x80,%ax
    303a:	50                   	push   %ax
    303b:	c4 5e 04             	les    0x4(%bp),%bx
    303e:	26 ff 77 2a          	push   %es:0x2a(%bx)
    3042:	26 ff 77 28          	push   %es:0x28(%bx)
    3046:	8b 46 f8             	mov    -0x8(%bp),%ax
    3049:	8b 56 fa             	mov    -0x6(%bp),%dx
    304c:	05 d0 00             	add    $0xd0,%ax
    304f:	52                   	push   %dx
    3050:	50                   	push   %ax
    3051:	e8 d8 d1             	call   0x22c
    3054:	83 c4 0a             	add    $0xa,%sp
    3057:	3d 00 00             	cmp    $0x0,%ax
    305a:	75 03                	jne    0x305f
    305c:	e9 3b 00             	jmp    0x309a
    305f:	c4 5e f8             	les    -0x8(%bp),%bx
    3062:	26 80 bf d0 00 5c    	cmpb   $0x5c,%es:0xd0(%bx)
    3068:	74 03                	je     0x306d
    306a:	e9 0e 00             	jmp    0x307b
    306d:	c4 5e f8             	les    -0x8(%bp),%bx
    3070:	26 80 bf d1 00 5c    	cmpb   $0x5c,%es:0xd1(%bx)
    3076:	75 03                	jne    0x307b
    3078:	e9 1f 00             	jmp    0x309a
    307b:	8b 46 f8             	mov    -0x8(%bp),%ax
    307e:	8b 56 fa             	mov    -0x6(%bp),%dx
    3081:	05 d0 00             	add    $0xd0,%ax
    3084:	52                   	push   %dx
    3085:	50                   	push   %ax
    3086:	ff 76 fa             	push   -0x6(%bp)
    3089:	ff 76 f8             	push   -0x8(%bp)
    308c:	e8 e7 d9             	call   0xa76
    308f:	83 c4 08             	add    $0x8,%sp
    3092:	3d 00 00             	cmp    $0x0,%ax
    3095:	74 03                	je     0x309a
    3097:	e9 17 00             	jmp    0x30b1
    309a:	b8 02 30             	mov    $0x3002,%ax
    309d:	ba 00 00             	mov    $0x0,%dx
    30a0:	52                   	push   %dx
    30a1:	50                   	push   %ax
    30a2:	ff 76 fa             	push   -0x6(%bp)
    30a5:	ff 76 f8             	push   -0x8(%bp)
    30a8:	e8 f4 d8             	call   0x99f
    30ab:	83 c4 08             	add    $0x8,%sp
    30ae:	e9 77 02             	jmp    0x3328
    30b1:	b8 80 00             	mov    $0x80,%ax
    30b4:	50                   	push   %ax
    30b5:	8b 46 f8             	mov    -0x8(%bp),%ax
    30b8:	8b 56 fa             	mov    -0x6(%bp),%dx
    30bb:	05 50 00             	add    $0x50,%ax
    30be:	52                   	push   %dx
    30bf:	50                   	push   %ax
    30c0:	e8 f6 d0             	call   0x1b9
    30c3:	83 c4 06             	add    $0x6,%sp
    30c6:	89 46 ea             	mov    %ax,-0x16(%bp)
    30c9:	89 46 ec             	mov    %ax,-0x14(%bp)
    30cc:	83 7e ec 00          	cmpw   $0x0,-0x14(%bp)
    30d0:	75 03                	jne    0x30d5
    30d2:	e9 36 00             	jmp    0x310b
    30d5:	c4 5e f8             	les    -0x8(%bp),%bx
    30d8:	8b 76 ec             	mov    -0x14(%bp),%si
    30db:	26 80 78 4f 5c       	cmpb   $0x5c,%es:0x4f(%bx,%si)
    30e0:	75 03                	jne    0x30e5
    30e2:	e9 26 00             	jmp    0x310b
    30e5:	c4 5e f8             	les    -0x8(%bp),%bx
    30e8:	8b 76 ec             	mov    -0x14(%bp),%si
    30eb:	26 80 78 4f 2f       	cmpb   $0x2f,%es:0x4f(%bx,%si)
    30f0:	75 03                	jne    0x30f5
    30f2:	e9 16 00             	jmp    0x310b
    30f5:	c4 5e f8             	les    -0x8(%bp),%bx
    30f8:	8b 76 ec             	mov    -0x14(%bp),%si
    30fb:	26 80 78 4f 3a       	cmpb   $0x3a,%es:0x4f(%bx,%si)
    3100:	75 03                	jne    0x3105
    3102:	e9 06 00             	jmp    0x310b
    3105:	ff 4e ec             	decw   -0x14(%bp)
    3108:	e9 c1 ff             	jmp    0x30cc
    310b:	83 7e ec 00          	cmpw   $0x0,-0x14(%bp)
    310f:	75 03                	jne    0x3114
    3111:	e9 be 00             	jmp    0x31d2
    3114:	b8 80 00             	mov    $0x80,%ax
    3117:	50                   	push   %ax
    3118:	8b 46 f8             	mov    -0x8(%bp),%ax
    311b:	8b 56 fa             	mov    -0x6(%bp),%dx
    311e:	05 50 00             	add    $0x50,%ax
    3121:	52                   	push   %dx
    3122:	50                   	push   %ax
    3123:	8b 46 f8             	mov    -0x8(%bp),%ax
    3126:	8b 56 fa             	mov    -0x6(%bp),%dx
    3129:	05 d0 00             	add    $0xd0,%ax
    312c:	52                   	push   %dx
    312d:	50                   	push   %ax
    312e:	e8 fb d0             	call   0x22c
    3131:	83 c4 0a             	add    $0xa,%sp
    3134:	83 7e ec 03          	cmpw   $0x3,-0x14(%bp)
    3138:	77 03                	ja     0x313d
    313a:	e9 0f 00             	jmp    0x314c
    313d:	c4 5e f8             	les    -0x8(%bp),%bx
    3140:	8b 76 ec             	mov    -0x14(%bp),%si
    3143:	26 c6 80 cf 00 00    	movb   $0x0,%es:0xcf(%bx,%si)
    3149:	e9 0c 00             	jmp    0x3158
    314c:	c4 5e f8             	les    -0x8(%bp),%bx
    314f:	8b 76 ec             	mov    -0x14(%bp),%si
    3152:	26 c6 80 d0 00 00    	movb   $0x0,%es:0xd0(%bx,%si)
    3158:	8b 46 f8             	mov    -0x8(%bp),%ax
    315b:	8b 56 fa             	mov    -0x6(%bp),%dx
    315e:	05 d0 00             	add    $0xd0,%ax
    3161:	52                   	push   %dx
    3162:	50                   	push   %ax
    3163:	ff 76 fa             	push   -0x6(%bp)
    3166:	ff 76 f8             	push   -0x8(%bp)
    3169:	e8 0a d9             	call   0xa76
    316c:	83 c4 08             	add    $0x8,%sp
    316f:	3d 00 00             	cmp    $0x0,%ax
    3172:	74 03                	je     0x3177
    3174:	e9 17 00             	jmp    0x318e
    3177:	b8 02 30             	mov    $0x3002,%ax
    317a:	ba 00 00             	mov    $0x0,%dx
    317d:	52                   	push   %dx
    317e:	50                   	push   %ax
    317f:	ff 76 fa             	push   -0x6(%bp)
    3182:	ff 76 f8             	push   -0x8(%bp)
    3185:	e8 17 d8             	call   0x99f
    3188:	83 c4 08             	add    $0x8,%sp
    318b:	e9 9a 01             	jmp    0x3328
    318e:	b8 80 00             	mov    $0x80,%ax
    3191:	50                   	push   %ax
    3192:	8b 4e f8             	mov    -0x8(%bp),%cx
    3195:	8b 56 fa             	mov    -0x6(%bp),%dx
    3198:	03 4e ec             	add    -0x14(%bp),%cx
    319b:	83 c1 50             	add    $0x50,%cx
    319e:	52                   	push   %dx
    319f:	51                   	push   %cx
    31a0:	8b 4e f8             	mov    -0x8(%bp),%cx
    31a3:	8b 56 fa             	mov    -0x6(%bp),%dx
    31a6:	81 c1 50 01          	add    $0x150,%cx
    31aa:	52                   	push   %dx
    31ab:	51                   	push   %cx
    31ac:	e8 7d d0             	call   0x22c
    31af:	83 c4 0a             	add    $0xa,%sp
    31b2:	b8 80 00             	mov    $0x80,%ax
    31b5:	50                   	push   %ax
    31b6:	8b 46 f8             	mov    -0x8(%bp),%ax
    31b9:	8b 56 fa             	mov    -0x6(%bp),%dx
    31bc:	05 50 01             	add    $0x150,%ax
    31bf:	52                   	push   %dx
    31c0:	50                   	push   %ax
    31c1:	8b 46 f8             	mov    -0x8(%bp),%ax
    31c4:	8b 56 fa             	mov    -0x6(%bp),%dx
    31c7:	05 50 00             	add    $0x50,%ax
    31ca:	52                   	push   %dx
    31cb:	50                   	push   %ax
    31cc:	e8 5d d0             	call   0x22c
    31cf:	83 c4 0a             	add    $0xa,%sp
    31d2:	b8 42 00             	mov    $0x42,%ax
    31d5:	50                   	push   %ax
    31d6:	b8 20 00             	mov    $0x20,%ax
    31d9:	ba 00 00             	mov    $0x0,%dx
    31dc:	52                   	push   %dx
    31dd:	50                   	push   %ax
    31de:	9a f0 2c 00 00       	lcall  $0x0,$0x2cf0
    31e3:	89 46 f2             	mov    %ax,-0xe(%bp)
    31e6:	3d 00 00             	cmp    $0x0,%ax
    31e9:	74 03                	je     0x31ee
    31eb:	e9 17 00             	jmp    0x3205
    31ee:	b8 09 00             	mov    $0x9,%ax
    31f1:	ba 00 00             	mov    $0x0,%dx
    31f4:	52                   	push   %dx
    31f5:	50                   	push   %ax
    31f6:	ff 76 fa             	push   -0x6(%bp)
    31f9:	ff 76 f8             	push   -0x8(%bp)
    31fc:	e8 a0 d7             	call   0x99f
    31ff:	83 c4 08             	add    $0x8,%sp
    3202:	e9 23 01             	jmp    0x3328
    3205:	ff 76 f2             	push   -0xe(%bp)
    3208:	9a 22 2d 00 00       	lcall  $0x0,$0x2d22
    320d:	89 46 fc             	mov    %ax,-0x4(%bp)
    3210:	89 56 fe             	mov    %dx,-0x2(%bp)
    3213:	0b d0                	or     %ax,%dx
    3215:	74 03                	je     0x321a
    3217:	e9 1f 00             	jmp    0x3239
    321a:	ff 76 f2             	push   -0xe(%bp)
    321d:	9a bd 32 00 00       	lcall  $0x0,$0x32bd
    3222:	b8 0a 00             	mov    $0xa,%ax
    3225:	ba 00 00             	mov    $0x0,%dx
    3228:	52                   	push   %dx
    3229:	50                   	push   %ax
    322a:	ff 76 fa             	push   -0x6(%bp)
    322d:	ff 76 f8             	push   -0x8(%bp)
    3230:	e8 6c d7             	call   0x99f
    3233:	83 c4 08             	add    $0x8,%sp
    3236:	e9 ef 00             	jmp    0x3328
    3239:	c4 5e fc             	les    -0x4(%bp),%bx
    323c:	26 c7 07 80 00       	movw   $0x80,%es:(%bx)
    3241:	26 c7 47 02 c8 80    	movw   $0x80c8,%es:0x2(%bx)
    3247:	b0 00                	mov    $0x0,%al
    3249:	c4 5e fc             	les    -0x4(%bp),%bx
    324c:	26 88 47 05          	mov    %al,%es:0x5(%bx)
    3250:	c4 5e fc             	les    -0x4(%bp),%bx
    3253:	26 88 47 07          	mov    %al,%es:0x7(%bx)
    3257:	c4 5e fc             	les    -0x4(%bp),%bx
    325a:	26 c6 47 09 46       	movb   $0x46,%es:0x9(%bx)
    325f:	c4 5e fc             	les    -0x4(%bp),%bx
    3262:	26 c6 47 0b 5a       	movb   $0x5a,%es:0xb(%bx)
    3267:	ff 76 f2             	push   -0xe(%bp)
    326a:	9a 9f 33 00 00       	lcall  $0x0,$0x339f
    326f:	8b 46 ee             	mov    -0x12(%bp),%ax
    3272:	8b 5e f0             	mov    -0x10(%bp),%bx
    3275:	8b cb                	mov    %bx,%cx
    3277:	d1 e3                	shl    $1,%bx
    3279:	d1 e3                	shl    $1,%bx
    327b:	03 d9                	add    %cx,%bx
    327d:	d1 e3                	shl    $1,%bx
    327f:	89 87 26 02          	mov    %ax,0x226(%bx)
    3283:	b8 ff ff             	mov    $0xffff,%ax
    3286:	ba 00 00             	mov    $0x0,%dx
    3289:	52                   	push   %dx
    328a:	50                   	push   %ax
    328b:	ff 36 1e 02          	push   0x21e
    328f:	9a 98 1a 00 00       	lcall  $0x0,$0x1a98
    3294:	89 46 f4             	mov    %ax,-0xc(%bp)
    3297:	89 56 f6             	mov    %dx,-0xa(%bp)
    329a:	8b 46 f6             	mov    -0xa(%bp),%ax
    329d:	0b 46 f4             	or     -0xc(%bp),%ax
    32a0:	74 03                	je     0x32a5
    32a2:	e9 1f 00             	jmp    0x32c4
    32a5:	b8 02 00             	mov    $0x2,%ax
    32a8:	ba 00 00             	mov    $0x0,%dx
    32ab:	52                   	push   %dx
    32ac:	50                   	push   %ax
    32ad:	ff 76 fa             	push   -0x6(%bp)
    32b0:	ff 76 f8             	push   -0x8(%bp)
    32b3:	e8 e9 d6             	call   0x99f
    32b6:	83 c4 08             	add    $0x8,%sp
    32b9:	ff 76 f2             	push   -0xe(%bp)
    32bc:	9a ef 32 00 00       	lcall  $0x0,$0x32ef
    32c1:	e9 64 00             	jmp    0x3328
    32c4:	ff 36 1e 02          	push   0x21e
    32c8:	ff 76 f2             	push   -0xe(%bp)
    32cb:	c4 5e 04             	les    0x4(%bp),%bx
    32ce:	26 ff 77 04          	push   %es:0x4(%bx)
    32d2:	ff 76 f6             	push   -0xa(%bp)
    32d5:	ff 76 f4             	push   -0xc(%bp)
    32d8:	9a be 1a 00 00       	lcall  $0x0,$0x1abe
    32dd:	89 46 e8             	mov    %ax,-0x18(%bp)
    32e0:	ff 76 f6             	push   -0xa(%bp)
    32e3:	ff 76 f4             	push   -0xc(%bp)
    32e6:	9a cc 1a 00 00       	lcall  $0x0,$0x1acc
    32eb:	ff 76 f2             	push   -0xe(%bp)
    32ee:	9a a7 33 00 00       	lcall  $0x0,$0x33a7
    32f3:	8b 5e f0             	mov    -0x10(%bp),%bx
    32f6:	8b c3                	mov    %bx,%ax
    32f8:	d1 e3                	shl    $1,%bx
    32fa:	d1 e3                	shl    $1,%bx
    32fc:	03 d8                	add    %ax,%bx
    32fe:	d1 e3                	shl    $1,%bx
    3300:	c7 87 26 02 00 00    	movw   $0x0,0x226(%bx)
    3306:	83 7e e8 00          	cmpw   $0x0,-0x18(%bp)
    330a:	7c 03                	jl     0x330f
    330c:	e9 19 00             	jmp    0x3328
    330f:	b8 02 00             	mov    $0x2,%ax
    3312:	ba 00 00             	mov    $0x0,%dx
    3315:	52                   	push   %dx
    3316:	50                   	push   %ax
    3317:	ff 76 fa             	push   -0x6(%bp)
    331a:	ff 76 f8             	push   -0x8(%bp)
    331d:	e8 7f d6             	call   0x99f
    3320:	83 c4 08             	add    $0x8,%sp
    3323:	c7 46 e8 00 00       	movw   $0x0,-0x18(%bp)
    3328:	c4 5e f8             	les    -0x8(%bp),%bx
    332b:	26 80 bf 50 02 00    	cmpb   $0x0,%es:0x250(%bx)
    3331:	75 03                	jne    0x3336
    3333:	e9 25 00             	jmp    0x335b
    3336:	ff 76 fa             	push   -0x6(%bp)
    3339:	ff 76 f8             	push   -0x8(%bp)
    333c:	e8 17 e8             	call   0x1b56
    333f:	83 c4 04             	add    $0x4,%sp
    3342:	b8 02 00             	mov    $0x2,%ax
    3345:	ba 00 00             	mov    $0x0,%dx
    3348:	52                   	push   %dx
    3349:	50                   	push   %ax
    334a:	ff 76 fa             	push   -0x6(%bp)
    334d:	ff 76 f8             	push   -0x8(%bp)
    3350:	e8 4c d6             	call   0x99f
    3353:	83 c4 08             	add    $0x8,%sp
    3356:	c7 46 e8 00 00       	movw   $0x0,-0x18(%bp)
    335b:	ff 76 fa             	push   -0x6(%bp)
    335e:	ff 76 f8             	push   -0x8(%bp)
    3361:	e8 08 d8             	call   0xb6c
    3364:	83 c4 04             	add    $0x4,%sp
    3367:	3d 00 00             	cmp    $0x0,%ax
    336a:	74 03                	je     0x336f
    336c:	e9 19 00             	jmp    0x3388
    336f:	b8 02 00             	mov    $0x2,%ax
    3372:	ba 00 00             	mov    $0x0,%dx
    3375:	52                   	push   %dx
    3376:	50                   	push   %ax
    3377:	ff 76 fa             	push   -0x6(%bp)
    337a:	ff 76 f8             	push   -0x8(%bp)
    337d:	e8 1f d6             	call   0x99f
    3380:	83 c4 08             	add    $0x8,%sp
    3383:	c7 46 e8 00 00       	movw   $0x0,-0x18(%bp)
    3388:	8b 5e f0             	mov    -0x10(%bp),%bx
    338b:	8b c3                	mov    %bx,%ax
    338d:	d1 e3                	shl    $1,%bx
    338f:	d1 e3                	shl    $1,%bx
    3391:	03 d8                	add    %ax,%bx
    3393:	d1 e3                	shl    $1,%bx
    3395:	c7 87 26 02 00 00    	movw   $0x0,0x226(%bx)
    339b:	ff 76 ee             	push   -0x12(%bp)
    339e:	9a cf 2a 00 00       	lcall  $0x0,$0x2acf
    33a3:	ff 76 ee             	push   -0x12(%bp)
    33a6:	9a 37 2d 00 00       	lcall  $0x0,$0x2d37
    33ab:	83 7e e8 00          	cmpw   $0x0,-0x18(%bp)
    33af:	7f 03                	jg     0x33b4
    33b1:	e9 06 00             	jmp    0x33ba
    33b4:	b8 01 00             	mov    $0x1,%ax
    33b7:	e9 03 00             	jmp    0x33bd
    33ba:	b8 00 00             	mov    $0x0,%ax
    33bd:	e9 00 00             	jmp    0x33c0
    33c0:	5e                   	pop    %si
    33c1:	5f                   	pop    %di
    33c2:	8b e5                	mov    %bp,%sp
    33c4:	5d                   	pop    %bp
    33c5:	c3                   	ret
    33c6:	1e                   	push   %ds
    33c7:	58                   	pop    %ax
    33c8:	90                   	nop
    33c9:	45                   	inc    %bp
    33ca:	55                   	push   %bp
    33cb:	8b ec                	mov    %sp,%bp
    33cd:	1e                   	push   %ds
    33ce:	8e d8                	mov    %ax,%ds
    33d0:	81 ec 00 00          	sub    $0x0,%sp
    33d4:	57                   	push   %di
    33d5:	56                   	push   %si
    33d6:	b8 00 00             	mov    $0x0,%ax
    33d9:	50                   	push   %ax
    33da:	ff 76 08             	push   0x8(%bp)
    33dd:	ff 76 06             	push   0x6(%bp)
    33e0:	e8 34 f7             	call   0x2b17
    33e3:	83 c4 06             	add    $0x6,%sp
    33e6:	e9 00 00             	jmp    0x33e9
    33e9:	5e                   	pop    %si
    33ea:	5f                   	pop    %di
    33eb:	83 ed 02             	sub    $0x2,%bp
    33ee:	8b e5                	mov    %bp,%sp
    33f0:	1f                   	pop    %ds
    33f1:	5d                   	pop    %bp
    33f2:	4d                   	dec    %bp
    33f3:	ca 04 00             	lret   $0x4
    33f6:	1e                   	push   %ds
    33f7:	58                   	pop    %ax
    33f8:	90                   	nop
    33f9:	45                   	inc    %bp
    33fa:	55                   	push   %bp
    33fb:	8b ec                	mov    %sp,%bp
    33fd:	1e                   	push   %ds
    33fe:	8e d8                	mov    %ax,%ds
    3400:	81 ec 00 00          	sub    $0x0,%sp
    3404:	57                   	push   %di
    3405:	56                   	push   %si
    3406:	b8 01 00             	mov    $0x1,%ax
    3409:	50                   	push   %ax
    340a:	ff 76 08             	push   0x8(%bp)
    340d:	ff 76 06             	push   0x6(%bp)
    3410:	e8 04 f7             	call   0x2b17
    3413:	83 c4 06             	add    $0x6,%sp
    3416:	e9 00 00             	jmp    0x3419
    3419:	5e                   	pop    %si
    341a:	5f                   	pop    %di
    341b:	83 ed 02             	sub    $0x2,%bp
    341e:	8b e5                	mov    %bp,%sp
    3420:	1f                   	pop    %ds
    3421:	5d                   	pop    %bp
    3422:	4d                   	dec    %bp
    3423:	ca                   	.byte 0xca
    3424:	04                   	.byte 0x4
