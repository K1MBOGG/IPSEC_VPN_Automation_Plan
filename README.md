# 🔐 Plan de Automatización IPSec VPN
**Fortigate ↔ Palo Alto**

---

## 📄 Estructura del Documento

El objetivo de este documento es presentar el diseño y el plan de implementación para la automatización de una VPN IPSec site-to-site entre un firewall Fortigate y un firewall Palo Alto.

El documento se divide en dos partes principales:

### 🧠 PART 1 — High-Level Design (HLD)
En esta sección se describen los aspectos de diseño de la solución, incluyendo:

- Arquitectura general  
- Decisiones de diseño  
- Supuestos y requerimientos  
- Consideraciones de red, seguridad y WAN  
- Parámetros de la VPN  
- Riesgos y desafíos  

Ir directo al Documento de Diseño: [HLD](#-part-1--high-level-design-hld-1)

---

### ⚙️ PART 2 — Network Implementation Plan (NIP)
En esta sección se detalla el proceso de implementación y validación, incluyendo:

- Parámetros de entrada (Source of Truth)  
- Workflow de automatización con Ansible  
- Pre-checks y post-checks  
- Deployment plan  
- Validación automatizada y testing  
- Rollback y monitoreo  

Ir directo al Plan de Implementacion: [NIP](#-part-2--network-implementation-plan-nip-1)

---

# 🧠 PART 1 — High-Level Design (HLD)

## 1. Introducción
En esta sección se describe el diseño de la solución para la implementación de una VPN IPSec site-to-site entre un firewall Fortigate y un firewall Palo Alto.

La automatización se plantea utilizando **Ansible** como framework principal de orquestación para:

- Pre-checks  
- Despliegue de configuración  
- Post-checks  
- Validación básica  

---

## 2. Alcance y Suposiciones
### 2.1 Alcance

El presente diseño contempla la automatización de la configuración de una VPN IPSec site-to-site entre un dispositivo Fortigate y un firewall Palo Alto.

El alcance incluye:

- Definición de parámetros de la VPN (IPs, subredes, Phase 1 / Phase 2)
- Diseño de conectividad entre redes locales
- Configuración de routing (static como base, con consideración de BGP)
- Definición de security policies necesarias para permitir el tráfico
- Consideraciones de NAT
- Validaciones pre y post implementación
- Testing de conectividad
- Automatización del proceso utilizando Ansible

Adicionalmente, se incluyen consideraciones de diseño relevantes para entornos productivos, tales como:

- Requisitos de WAN / ISP
- Impacto de MTU / MSS
- QoS
- Escalabilidad y alta disponibilidad

---

### 2.2 Fuera de Alcance

Los siguientes puntos no forman parte del alcance directo de este documento:

- Implementación de HA (High Availability) 
- Integración con plataformas externas de monitoreo  
- Implementación de SD-WAN  
- Hardening avanzado de seguridad


---

### 2.3 Suposiciones

Para el correcto funcionamiento del diseño, se asumen las siguientes condiciones:

- Existe conectividad IP entre ambos extremos.  
- Las IPs públicas de ambos dispositivos son alcanzables a través de Internet.
- No existen restricciones intermedias que bloqueen tráfico IPsec (UDP 500/4500, ESP)  
- Los dispositivos cuentan con recursos suficientes para soportar tráfico cifrado. 
- Se dispone de credenciales válidas para acceso a los dispositivos (Ansible/API Key/SSH)  
- Las interfaces WAN están correctamente configuradas y operativas  
- No existe overlapping entre las subredes locales de ambos sitios  
- Se utilizarán parámetros compatibles de Phase 1 y Phase 2 en ambos extremos  

---

### 2.4 Consideraciones Iniciales

- Se adopta un enfoque de **route-based VPN** por su mayor flexibilidad y escalabilidad  
- Se utilizará **Ansible** como herramienta principal de automatización para garantizar consistencia y repetibilidad  
- El diseño está preparado para evolucionar hacia un esquema con routing dinámico utilizando BGP.  
---

## 3. Arquitectura General
### 3.1 Descripción General

La solución consiste en una VPN IPSec site-to-site entre un firewall Fortigate y un firewall Palo Alto, utilizando un enfoque de **route-based VPN** sobre Internet como medio de transporte.

El túnel IPSec actúa como un enlace lógico entre ambos dispositivos, permitiendo la interconexión segura de las redes locales de cada sitio.


### 3.2 Topología Lógica

La topología se compone de dos dominios de red independientes conectados a través de Internet:

```bash 
[LAN Fortigate] --- Fortigate --- Internet --- Palo Alto --- [LAN Palo Alto]
```
                        |--------- IPSec Tunnel ---------|

Cada dispositivo cuenta con:

- Una interfaz WAN con IP pública
- Una o más redes LAN internas
- Una interfaz de túnel (tunnel interface) asociada a la VPN IPSec

---

### 3.3 Componentes de la Solución

Los principales componentes del diseño son:

- **IPSec Tunnel:** canal cifrado entre ambos dispositivos
- **Tunnel Interface:** interfaz lógica utilizada para routing
- **Routing:** definición del tráfico que debe cruzar el túnel
- **Security Policies:** reglas que permiten el tráfico entre zonas
- **NAT Policies:** reglas de NAT exemption para tráfico VPN

---

### 3.4 Flujo de Tráfico

El flujo de tráfico se comporta de la siguiente manera:

1. Un host en la LAN del Fortigate envía tráfico hacia la red remota
2. El firewall evalúa la tabla de routing
3. El tráfico es dirigido hacia la interfaz de túnel
4. El tráfico es encapsulado y cifrado mediante IPsec
5. El tráfico atraviesa Internet
6. El firewall Palo Alto recibe y descifra el tráfico
7. El tráfico es reenviado hacia la red LAN destino

El flujo en sentido inverso sigue el mismo proceso.

---

### 3.5 Consideraciones de Diseño

- El túnel se implementa como **route-based**, permitiendo desacoplar la configuración de IPsec del routing
- El diseño permite la incorporación futura de **routing dinámico (BGP over IPsec)**
- Se considera una arquitectura inicial de **single tunnel**, con posibilidad de evolución hacia esquemas de alta disponibilidad (dual tunnel / multi-ISP)
- El tráfico es controlado mediante políticas de seguridad en ambos extremos

---

### 3.6 Escalabilidad

El diseño está preparado para soportar:

- Adición de nuevas subredes sin modificar la configuración base del túnel
- Migración hacia routing dinámico (BGP)
- Implementación de múltiples túneles para redundancia
- Integración con soluciones más avanzadas (ej: SD-WAN)

---
---

## 4. Requisitos de Conectividad

### 4.1 Redes Locales

Se definen las redes locales que serán interconectadas a través del túnel IPSec.

- **Sitio Fortigate (Local Site):**
  - Subred(es): [definir]

- **Sitio Palo Alto (Remote Site):**
  - Subred(es): [definir]

Estas redes deben ser **no superpuestas (non-overlapping)** para evitar conflictos de routing y garantizar una correcta comunicación.

---

### 4.2 Tipo de Tráfico

El túnel IPSec permitirá el intercambio de tráfico entre las redes definidas, considerando:

- Tráfico de aplicaciones internas (ej: aplicaciones corporativas)
- Acceso a servicios remotos (ej: servidores, bases de datos)
- Tráfico administrativo (opcional)
- ICMP para testing y validación

Se recomienda evitar configuraciones tipo **any-to-any** y aplicar el principio de **least privilege**, permitiendo únicamente el tráfico necesario.

---

### 4.3 Dirección del Tráfico

La conectividad será:

- **Bi-direccional**, permitiendo comunicación desde ambos sitios
- Controlada mediante **security policies** en cada firewall

---

### 4.4 Clasificación del Tráfico

Para fines de diseño, el tráfico puede clasificarse como:

- **Crítico:** aplicaciones sensibles a latencia como VOIP o sistemas criticos.
- **No crítico:** tráfico de usuario general.

Esta clasificación es relevante para futuras consideraciones de **QoS** y priorización.

---

### 4.5 Requerimientos de Disponibilidad

- Se espera que la conectividad entre sitios esté disponible de forma continua
- El diseño inicial considera un único túnel, con posibilidad de evolución hacia esquemas redundantes (dual tunnel / multi-ISP)

---

### 4.6 Consideraciones de Seguridad

- El tráfico entre sitios debe estar cifrado mediante IPsec
- El acceso entre redes debe estar restringido mediante políticas de firewall
- Se debe habilitar logging para tráfico relevante

---

### 4.7 Consideraciones Operativas

- Se deben definir mecanismos de validación de conectividad (ping, traceroute)
- Se debe poder verificar fácilmente qué tráfico está utilizando el túnel
- Se recomienda mantener visibilidad del tráfico para troubleshooting

---

## 5. Requisitos WAN / ISP 

### 5.1 Descripción General

La VPN IPSec se establece sobre Internet como medio de transporte, por lo que el comportamiento del túnel depende directamente de las características de los enlaces WAN y de los proveedores de servicio (ISP).

Por este motivo, es fundamental considerar aspectos de capacidad, calidad y resiliencia del enlace.

---

### 5.2 Cantidad de Enlaces

Cada sitio puede contar con:

- **Single ISP:**
  - Implementación simple
  - Sin redundancia

- **Dual ISP :**
  - Mayor resiliencia
  - Posibilidad de failover o balanceo
  - Reducción de dependencia de un único proveedor

---

### 5.3 Requerimientos de Capacidad

El ancho de banda del enlace debe dimensionarse considerando:

- Tráfico esperado entre sitios  
- Crecimiento futuro  
- Overhead introducido por IPsec  
- Capacidad real de cifrado del firewall (IPsec throughput)

Es importante destacar que:

- El throughput efectivo puede ser menor al nominal del enlace debido al cifrado  
- La performance del túnel depende de CPU/ASIC del dispositivo  

---

### 5.4 SLA del ISP

Los siguientes parámetros deben ser considerados:

- **Latency**
- **Jitter**
- **Packet Loss**

Estos factores impactan directamente en:

- Performance de aplicaciones  
- Calidad de voz/video  
- Estabilidad del túnel  

En Internet, estos valores no están garantizados, por lo que el diseño debe contemplar variabilidad.

---

### 5.5 Requisitos de Direccionamiento Público

- Se recomienda el uso de **IP públicas estáticas** en ambos extremos  
- En caso de IP dinámica:
  - Se requiere mecanismos adicionales (ej: DDNS)
  - Mayor complejidad operativa  

---

### 5.6 Consideraciones de NAT

- Se debe validar si existe NAT en el camino (ej: CGNAT)  
- En caso de NAT:
  - Se utilizará **NAT-T (UDP 4500)**  
- Es necesario permitir:
  - UDP 500 (IKE)  
  - UDP 4500 (NAT-T)  
  - ESP (si no hay NAT)  

---

### 5.7 Consideraciones de MTU

El enlace WAN puede verse afectado por:

- Overhead de IPsec  
- Encapsulaciones adicionales 

Esto puede generar:

- Fragmentación  
- Degradación de performance  

Se recomienda:

- Evaluar MTU efectiva  
- Considerar ajuste de MSS  
- Validar comportamiento de PMTUD  

---

### 5.8 Resiliencia y Redundancia

Para entornos productivos, se recomienda:

- Uso de múltiples enlaces WAN (multi-ISP)  
- Implementación de túneles redundantes  
- Mecanismos de failover  

Opciones de implementación:

- Túnel primario / secundario  
- Routing dinámico (BGP)  
- Monitoreo de estado del túnel  

---

### 5.9 Consideraciones de QoS en WAN

Dado que la VPN opera sobre Internet:

- No es posible garantizar QoS end-to-end  
- Sin embargo, se pueden aplicar políticas de QoS en el egress del firewall  

Objetivos:

- Priorizar tráfico crítico  
- Evitar congestión local  
- Optimizar uso del enlace  

---

### 5.10 Consideraciones de Diseño

- Internet debe considerarse como un medio **best-effort**  
- La calidad del servicio depende del ISP  
- El diseño debe contemplar variabilidad y posibles degradaciones  
- La resiliencia debe lograrse mediante redundancia, no mediante suposiciones de calidad  

---

## 6. Diseño de la VPN

### 6.1 Tipo de Túnel

Se implementa una **route-based VPN**, en la cual el túnel IPSec se representa como una interfaz lógica (tunnel interface).

Este enfoque permite:

- Desacoplar la configuración del túnel de las redes transportadas  
- Utilizar routing (static o dinámico) para definir el tráfico  
- Facilitar la escalabilidad y operación  
- Habilitar integración con protocolos de routing dinámico (ej: BGP)  

---

### 6.2 Plan de Direccionamiento (Addressing Plan)

Se define un esquema de direccionamiento para:

- Interfaces WAN (IPs públicas)  
- Redes LAN en cada sitio  
- Red de túnel (transit network /30)  

Ejemplo:

- Red de túnel: 169.254.1.0/30  
  - Fortigate: 169.254.1.1/30  
  - Palo Alto: 169.254.1.2/30  

La red de túnel se utiliza para:

- Routing entre dispositivos  
- Posible uso de protocolos dinámicos (BGP)

---

### 6.3 IKE (Phase 1)

La fase 1 (IKE) se encarga de establecer el canal seguro inicial entre ambos dispositivos.

Parámetros recomendados:

- **Versión:** IKEv2  
- **Encryption:** AES-256  
- **Integrity:** SHA-256  
- **DH Group:** 14 (o superior)  
- **Authentication:** Pre-Shared Key (PSK)  
- **Lifetime:** 28800 segundos  

Consideraciones:

- IKEv2 ofrece mejor eficiencia y estabilidad que IKEv1  
- Los parámetros deben coincidir exactamente en ambos extremos  

---

### 6.4 IPsec (Phase 2)

La fase 2 define cómo se cifra el tráfico de datos.

Parámetros recomendados:

- **Encryption:** AES-256  
- **Integrity:** SHA-256  
- **PFS (Perfect Forward Secrecy):** DH Group 14  
- **Lifetime:** 3600 segundos  

Consideraciones:

- Se recomienda habilitar PFS para mayor seguridad  
- En un diseño route-based, los selectors pueden ser más amplios (ej: 0.0.0.0/0)

---

### 6.5 NAT Traversal (NAT-T)

En caso de existir NAT en el camino:

- Se utilizará **NAT-T (UDP 4500)**  
- El tráfico IPsec será encapsulado en UDP  

Consideraciones:

- Requiere permitir UDP 500 y 4500 en ambos extremos  
- Es común en entornos con NAT intermedio  

---

### 6.6 Parámetros de Seguridad

- Uso de algoritmos modernos (AES-256, SHA-256)  
- Uso de DH Group seguro  
- Uso de PFS  
- Uso de PSK robusto (o certificados en entornos productivos)  

---

### 6.7 Consideraciones Multi-Vendor

Dado que la VPN se establece entre diferentes fabricantes, es importante considerar:

- Coincidencia exacta de parámetros Phase 1 y Phase 2  
- Diferencias en nomenclatura de configuraciones  
- Comportamiento distinto en proxy-IDs / selectors  
- Diferencias en manejo de lifetimes y rekey  

---

### 6.8 Escalabilidad del Diseño

El diseño permite:

- Agregar nuevas redes sin modificar el túnel  
- Implementar routing dinámico (BGP)  
- Incorporar túneles adicionales para redundancia  
- Evolucionar hacia arquitecturas más complejas  

---

## 7. Diseño de Routing

### 7.1 Descripción General

El routing determina qué tráfico debe ser enviado a través del túnel IPSec.  
En un diseño **route-based VPN**, el tráfico se dirige hacia la interfaz de túnel en función de la tabla de routing.

Se consideran dos enfoques:

- Routing estático (baseline)
- Routing dinámico (BGP over IPsec)

---

### 7.2 Routing Estático

En el enfoque baseline, se configuran rutas estáticas en ambos dispositivos.

Ejemplo:

- En Fortigate:
  - Ruta hacia la red remota vía interfaz de túnel  

- En Palo Alto:
  - Ruta hacia la red remota vía interfaz de túnel  

Ventajas:

- Implementación simple  
- Fácil de entender y configurar  
- Adecuado para entornos pequeños o con pocas redes  

Limitaciones:

- Escalabilidad limitada  
- Requiere cambios manuales al agregar nuevas subredes  
- No detecta dinámicamente fallas de camino  

---

### 7.3 Routing Dinámico (BGP over IPsec)

Como mejora del diseño, se propone el uso de **BGP sobre el túnel IPSec**.

En este modelo:

- Se establece una sesión BGP entre ambos extremos usando las IPs del túnel (/30)  
- Se intercambian rutas dinámicamente  

Ventajas:

- Escalabilidad  
- Reducción de configuración manual  
- Adaptación automática ante cambios de red  
- Mejor integración con escenarios de redundancia  

---

### 7.4 Consideraciones de BGP

- Uso de direcciones de túnel como endpoints BGP  
- Configuración de vecinos (neighbors) en ambos extremos  
- Definición de políticas de import/export  
- Filtrado de prefijos para evitar anuncios incorrectos  
- Control de rutas (ej: local preference, MED)  

---

### 7.5 Failover y Resiliencia

El routing juega un rol clave en escenarios de alta disponibilidad.

Opciones:

- Uso de múltiples túneles (primary / secondary)  
- Implementación de BGP para detección automática de fallas  
- Monitoreo de reachability del túnel  

Consideraciones:

- Evitar blackholing de tráfico  
- Garantizar convergencia rápida  
- Validar comportamiento ante caída del túnel  

---

### 7.6 Consideraciones de Diseño

- Routing estático es suficiente para un escenario inicial simple  
- BGP es recomendado para entornos productivos o escalables  
- El uso de route-based VPN permite integrar fácilmente routing dinámico  
- Se debe evitar asimetría de tráfico  

---

### 7.7 Recomendación

Para este diseño:

- Se implementa **static routing** como baseline  
- Se documenta **BGP over IPsec** como evolución recomendada  

Esto permite cumplir con los requerimientos del challenge manteniendo un diseño preparado para crecimiento futuro.
---

## 8. Diseño de Seguridad

### 8.1 Descripción General

La implementación de la VPN IPSec no implica automáticamente la habilitación de tráfico entre las redes.  
El acceso entre sitios debe ser explícitamente permitido mediante políticas de seguridad en ambos dispositivos.

El diseño de seguridad se basa en el principio de **least privilege**, permitiendo únicamente el tráfico necesario.

---

### 8.2 Modelo de Zonas (Zone-Based Design)

Cada dispositivo utiliza un modelo basado en zonas para controlar el tráfico.

Ejemplo:

- Zona LAN  
- Zona VPN (tunnel interface)  
- Zona WAN  

El tráfico entre zonas debe ser autorizado mediante políticas específicas.

---

### 8.3 Políticas de Seguridad (Security Policies)

Se deben definir políticas que permitan:

- Tráfico desde LAN local hacia LAN remota  
- Tráfico desde LAN remota hacia LAN local  

Las políticas deben especificar:

- Origen (source zone / subnet)  
- Destino (destination zone / subnet)  
- Aplicaciones o puertos permitidos  
- Acción (allow)  
- Logging habilitado  

---

### 8.4 Principio de Least Privilege

Se recomienda:

- Evitar configuraciones tipo **any-to-any**  
- Permitir únicamente aplicaciones o servicios necesarios  
- Restringir acceso administrativo  

Esto reduce la superficie de ataque y mejora el control del tráfico.

---

### 8.5 Logging y Visibilidad

Es importante habilitar logging en:

- Políticas de seguridad relevantes  
- Eventos de VPN (IKE / IPsec)  

Esto permite:

- Auditoría de tráfico  
- Troubleshooting  
- Detección de anomalías  

---

### 8.6 Consideraciones de Inspección

Dependiendo del entorno, se puede considerar:

- Inspección de aplicaciones  
- Inspección SSL (si aplica)  

Sin embargo, en túneles VPN:

- Puede ser necesario excluir cierto tráfico de inspección para evitar impacto en performance  

---

### 8.7 Consideraciones de Control de Acceso

- Definir claramente qué redes pueden comunicarse  
- Limitar acceso entre segmentos sensibles  
- Evitar exposición innecesaria de servicios  

---

### 8.8 Consideraciones Multi-Vendor

Dado el uso de diferentes plataformas:

- La lógica de políticas puede diferir entre Fortigate y Palo Alto  
- La definición de zonas y reglas debe ser consistente en ambos extremos  
- Se debe validar que ambas configuraciones permitan el flujo esperado  

---

### 8.9 Consideraciones de Diseño

- La VPN provee cifrado, pero no control de acceso  
- El control de acceso se define mediante políticas de firewall  
- La visibilidad del tráfico es clave para operación y troubleshooting  
---

## 9. Consideraciones de NAT

### 9.1 Descripción General

El uso de NAT (Network Address Translation) puede impactar directamente el funcionamiento de la VPN IPSec.

Es fundamental identificar si el tráfico entre sitios debe ser traducido o no, y configurar correctamente las políticas de NAT para evitar problemas de conectividad.

---

### 9.2 NAT Exemption (No-NAT)

Para el correcto funcionamiento de la VPN, el tráfico entre las redes locales debe excluirse de NAT.

Esto se conoce como:

- NAT exemption  
- No-NAT rule  
- Identity NAT  

Ejemplo:

- Tráfico desde LAN local hacia LAN remota → **no debe ser NATeado**

Consideraciones:

- La regla de no-NAT debe evaluarse antes que otras reglas de NAT  
- La falta de NAT exemption puede provocar fallas en la VPN  

---

### 9.3 NAT Traversal (NAT-T)

En caso de que exista NAT en el camino entre los extremos:

- Se utilizará **NAT-T (UDP 4500)**  
- El tráfico IPsec será encapsulado en UDP  

Requisitos:

- Permitir UDP 500 (IKE)  
- Permitir UDP 4500 (NAT-T)  

Consideraciones:

- NAT-T es común en entornos con NAT intermedio  
- Puede introducir overhead adicional  

---

### 9.4 NAT en el Flujo de Tráfico

El orden correcto del procesamiento es crítico:

1. Evaluación de políticas de seguridad  
2. Aplicación de NAT (si corresponde)  
3. Encapsulación IPsec  

El tráfico debe coincidir con los parámetros esperados por el túnel IPsec.

---

### 9.5 Redes Superpuestas (Overlapping Subnets)

En caso de que existan subredes superpuestas entre los sitios, no es posible utilizar routing directo.

Como solución, se puede implementar un esquema de NAT:

- Traducción de una de las redes a una subred no superpuesta  
- Uso de una red "virtual" para el tráfico a través del túnel  

Ejemplo:

- Red real: 10.10.10.0/24  
- Red traducida: 172.16.10.0/24  

Consideraciones:

- Aumenta la complejidad operativa  
- Impacta troubleshooting y logging  
- Requiere consistencia en ambos extremos  

Se recomienda evitar subredes superpuestas cuando sea posible.

---

### 9.6 Consideraciones Multi-Vendor

El comportamiento de NAT puede diferir entre plataformas:

- Fortigate:
  - NAT integrado en firewall policies o central NAT  

- Palo Alto:
  - NAT definido mediante reglas específicas separadas  

Se debe asegurar consistencia en:

- Orden de evaluación  
- Traducción aplicada  
- Correspondencia de políticas  

---

### 9.7 Consideraciones de Diseño

- El tráfico VPN debe excluirse de NAT  
- NAT-T debe considerarse en entornos con NAT intermedio  
- NAT debe ser cuidadosamente diseñado para evitar conflictos  
- Se debe validar el comportamiento de NAT durante troubleshooting  

---

## 10. Consideraciones de MTU / MSS

### 10.1 Descripción General

El uso de IPSec introduce overhead adicional debido a la encapsulación del tráfico, lo que impacta directamente en el tamaño máximo de paquete (MTU).

Si este aspecto no es correctamente considerado, pueden producirse problemas de:

- Fragmentación  
- Degradación de performance  
- Fallas intermitentes en aplicaciones  

---

### 10.2 Overhead de IPsec

Cuando un paquete es encapsulado en IPsec, se agregan múltiples encabezados:

- Nuevo header IP (outer IP)  
- Encabezado ESP  
- Posible encapsulación UDP (NAT-T)  
- Padding y autenticación  

Esto reduce el tamaño efectivo del payload.

---

### 10.3 Impacto en MTU

El MTU efectivo del túnel es menor que el MTU del enlace físico.

Ejemplo:

- MTU estándar: 1500 bytes  
- MTU efectiva con IPsec: menor a 1500 (dependiendo de encapsulación)

Consecuencias:

- Paquetes grandes pueden fragmentarse  
- Si el bit DF (Don't Fragment) está activo, los paquetes pueden descartarse  

---

### 10.4 Ajuste de MSS (Maximum Segment Size)

Una práctica común es ajustar el MSS para evitar fragmentación.

Esto permite:

- Reducir el tamaño de los segmentos TCP  
- Evitar que los paquetes excedan el MTU efectivo del túnel  

El ajuste de MSS se realiza típicamente en:

- Interfaces de túnel  
- Políticas de firewall  

---

### 10.5 PMTUD (Path MTU Discovery)

El mecanismo PMTUD permite a los hosts descubrir el MTU máximo del camino.

Sin embargo:

- Puede fallar si los mensajes ICMP están bloqueados  
- Puede generar problemas de conectividad difíciles de diagnosticar  

---

### 10.6 Recomendaciones

- Evaluar el MTU efectivo del túnel  
- Implementar ajuste de MSS cuando sea necesario  
- Permitir ICMP para correcto funcionamiento de PMTUD  
- Validar comportamiento mediante testing (ping con tamaño específico)  

---

### 10.7 Consideraciones de Diseño

- MTU/MSS es un factor crítico para la estabilidad del túnel  
- Problemas de MTU pueden manifestarse como fallas intermitentes  
- Este aspecto debe ser considerado desde el diseño y validado en la implementación  

---

## 11. Consideraciones de QoS

### 11.1 Descripción General

La VPN IPSec se establece sobre Internet como medio de transporte, por lo que no es posible garantizar calidad de servicio (QoS) end-to-end debido a la falta de control sobre la red intermedia (ISP).

Sin embargo, es posible implementar mecanismos de QoS en los extremos (firewalls) para optimizar el uso del enlace y mejorar el comportamiento del tráfico.

---

### 11.2 Objetivos de QoS

El objetivo de QoS en este diseño no es garantizar performance, sino:

- Priorizar tráfico crítico  
- Evitar congestión en el enlace WAN  
- Proteger aplicaciones sensibles (ej: voz, control traffic)  
- Limitar impacto de tráfico no crítico (ej: backup, bulk traffic)  

---

### 11.3 QoS en el Edge (Egress)

QoS se aplica principalmente en el punto de salida (egress) hacia el enlace WAN.

En este punto es posible:

- Clasificar tráfico  
- Priorizar paquetes  
- Aplicar traffic shaping o rate limiting  

Esto permite controlar el comportamiento del tráfico antes de ser encapsulado en el túnel IPSec.

---

### 11.4 Clasificación de Tráfico

El tráfico puede clasificarse en diferentes categorías:

- **Alta prioridad:** VoIP, control traffic  
- **Media prioridad:** aplicaciones críticas  
- **Baja prioridad:** tráfico de usuario general  
- **Muy baja prioridad:** backup, transferencias masivas  

---

### 11.5 Marcado DSCP

Se puede utilizar DSCP para marcar el tráfico antes de encapsularlo.

Consideraciones:

- El valor DSCP puede ser preservado dentro del túnel  
- El dispositivo remoto puede utilizarlo para aplicar políticas de QoS  

Sin embargo:

- No existe garantía de que el ISP respete el marcado DSCP  
- El comportamiento en Internet sigue siendo best-effort  

---

### 11.6 Limitaciones

- No se puede garantizar latencia, jitter o packet loss en Internet  
- El ISP puede ignorar o modificar DSCP  
- QoS no controla la red intermedia  

---

### 11.7 Beneficios

A pesar de sus limitaciones, QoS permite:

- Mejorar la experiencia de aplicaciones críticas  
- Evitar congestión causada por tráfico interno  
- Optimizar el uso del enlace WAN  
- Preparar el diseño para futuras mejoras (ej: SD-WAN, MPLS)  

---

### 11.8 Consideraciones de Diseño

- QoS debe entenderse como un mecanismo de optimización local  
- El control efectivo del tráfico se realiza en el edge  
- El diseño debe considerar QoS como complemento, no como garantía  

---

## 12. Alta Disponibilidad (High Availability)

### 12.1 Descripción General

La alta disponibilidad (HA) es un aspecto clave en entornos productivos, especialmente cuando la conectividad entre sitios es crítica.

El diseño inicial considera una implementación básica con un único túnel IPSec, pero contempla la posibilidad de evolucionar hacia arquitecturas redundantes.

---

### 12.2 Escenario Base (Single Tunnel)

En el escenario inicial:

- Se establece un único túnel IPSec entre ambos sitios  
- La conectividad depende de un único enlace WAN  

Limitaciones:

- Punto único de falla (single point of failure)  
- Interrupción total ante caída del túnel o del enlace  

---

### 12.3 Escenarios de Redundancia

Para mejorar la resiliencia, se pueden considerar los siguientes enfoques:

#### a) Dual Tunnel

- Configuración de múltiples túneles IPSec entre los mismos dispositivos  
- Túneles primary / secondary  

#### b) Multi-ISP

- Cada sitio dispone de más de un proveedor de Internet  
- Reducción del riesgo de falla por proveedor  

#### c) Combinación Dual Tunnel + Multi-ISP

- Mayor nivel de resiliencia  
- Posibilidad de múltiples caminos de comunicación  

---

### 12.4 Mecanismos de Failover

El failover puede implementarse mediante:

- Routing estático con métricas (distance / priority)  
- Monitoreo de estado del túnel  
- Routing dinámico (BGP)  

Consideraciones:

- El failover debe ser automático  
- Se debe evitar blackholing de tráfico  
- Se debe validar el tiempo de convergencia  

---

### 12.5 Uso de BGP para Resiliencia

El uso de **BGP over IPsec** permite:

- Detección automática de fallas  
- Retiro dinámico de rutas  
- Selección de mejor camino  

Esto mejora significativamente la resiliencia del diseño.

---

### 12.6 Consideraciones de Diseño

- La alta disponibilidad no debe depender de un único enlace  
- La redundancia debe implementarse a nivel de red (WAN) y túnel  
- El diseño debe contemplar escenarios de falla y recuperación  
- Se deben realizar pruebas de failover  

---

### 12.7 Limitaciones

- El escenario de HA completo no forma parte del alcance inicial  
- Se documenta como mejora futura del diseño  

---

## 13. Monitoreo y Observabilidad

### 13.1 Descripción General

La observabilidad es fundamental para garantizar la operación continua de la VPN IPSec.

No es suficiente con que el túnel esté configurado; es necesario poder:

- Verificar su estado  
- Monitorear el tráfico  
- Detectar fallas  
- Facilitar troubleshooting  

---

### 13.2 Monitoreo del Túnel

Se deben monitorear los siguientes elementos:

- Estado de IKE (Phase 1)  
- Estado de IPsec (Phase 2)  
- Número de Security Associations (SA) activas  
- Eventos de rekey  

Esto permite identificar:

- Caídas del túnel  
- Problemas de negociación  
- Inestabilidad  

---

### 13.3 Monitoreo de Tráfico

Se debe observar:

- Bytes y paquetes transmitidos  
- Uso del túnel  
- Incremento de counters  

Esto permite validar:

- Que el túnel está siendo utilizado  
- Comportamiento del tráfico  
- Posibles congestiones  

---

### 13.4 Monitoreo de Routing

Se deben verificar:

- Presencia de rutas hacia redes remotas  
- Estado de la tabla de routing  
- Sesión BGP (si aplica)  

Esto es clave para detectar:

- Falta de rutas  
- Problemas de convergencia  
- Inconsistencias de routing  

---

### 13.5 Logging

Se recomienda habilitar logs para:

- Eventos de VPN (IKE/IPsec)  
- Políticas de seguridad  
- Eventos de NAT  

Los logs permiten:

- Auditoría  
- Troubleshooting  
- Detección de anomalías  

---

### 13.6 Alertas

Se deben definir alertas para:

- Túnel down  
- Falta de tráfico en el túnel  
- Pérdida de rutas  
- Fallas de negociación IPsec  

Esto permite una respuesta rápida ante incidentes.

---

### 13.7 Validación Operativa

Se deben implementar mecanismos de validación periódica:

- Ping entre tunnel IPs  
- Ping entre redes LAN  
- Traceroute  

Esto permite confirmar conectividad real (data plane).

---

### 13.8 Consideraciones de Diseño

- El estado del túnel no garantiza conectividad real  
- Es necesario validar tanto control plane como data plane  
- La visibilidad es clave para operación eficiente  
- El diseño debe facilitar troubleshooting  
 
---

## 14. Consideraciones Multi-Vendor

### 14.1 Descripción General

La implementación de una VPN IPSec entre dispositivos de distintos fabricantes (Fortigate y Palo Alto) introduce desafíos adicionales debido a diferencias en:

- Implementación de protocolos  
- Nomenclatura de configuraciones  
- Comportamiento por defecto  

Es fundamental garantizar compatibilidad total entre ambos extremos.

---

### 14.2 Compatibilidad de Phase 1 y Phase 2

Los parámetros de IKE (Phase 1) e IPsec (Phase 2) deben coincidir exactamente en ambos dispositivos:

- Encryption  
- Integrity  
- DH Group  
- Lifetime  
- PFS  

Cualquier discrepancia puede provocar:

- Fallas en la negociación  
- Túnel no establecido  
- Inestabilidad  

---

### 14.3 Proxy-ID vs Route-Based

Diferencias clave:

- **Palo Alto:**
  - Puede requerir definición explícita de proxy-IDs  
  - Puede trabajar en modo policy-based o route-based  

- **Fortigate:**
  - Soporta route-based de forma nativa  
  - Puede utilizar selectors amplios  

Consideraciones:

- En route-based VPN, se recomienda utilizar selectors amplios (ej: 0.0.0.0/0)  
- Se debe validar que ambos dispositivos interpreten correctamente el tráfico esperado  

---

### 14.4 Diferencias en NAT

- Fortigate:
  - NAT puede estar integrado en firewall policies  

- Palo Alto:
  - NAT se configura mediante reglas separadas  

Esto requiere:

- Alinear el comportamiento de NAT en ambos extremos  
- Verificar el orden de evaluación de reglas  

---

### 14.5 Diferencias en Routing

- Implementación de routing puede variar entre dispositivos  
- Configuración de interfaces de túnel y virtual routers puede diferir  

Se debe asegurar:

- Consistencia en rutas configuradas  
- Correcta asociación del túnel a la tabla de routing  

---

### 14.6 Diferencias en Logging y Debugging

- Comandos de diagnóstico difieren entre fabricantes  
- Formato de logs y eventos puede variar  

Esto impacta:

- Troubleshooting  
- Análisis de problemas  

---

### 14.7 Diferencias en APIs y Automatización

- Fortigate:
  - API REST estructurada  

- Palo Alto:
  - Uso de REST API y/o XML API  

Consideraciones:

- Los módulos de Ansible abstraen estas diferencias  
- Es importante validar que las operaciones sean consistentes en ambos dispositivos  

---

### 14.8 Consideraciones de Diseño

- La interoperabilidad requiere alineación estricta de parámetros  
- Se debe validar la configuración en ambos extremos  
- El troubleshooting puede ser más complejo en entornos multi-vendor  
- La automatización debe contemplar diferencias entre plataformas  

---

## 15. Riesgos y Desafíos

### 15.1 Descripción General

La implementación de una VPN IPSec entre dispositivos de distintos fabricantes presenta diversos riesgos técnicos y operativos que deben ser considerados desde la etapa de diseño.

La identificación de estos riesgos permite reducir impacto y mejorar la resiliencia del despliegue.

---

### 15.2 Riesgos de Configuración

- Mismatch en parámetros de Phase 1 / Phase 2  
- Errores en configuración de routing  
- Falta de NAT exemption  
- Definición incorrecta de security policies  

Impacto:

- Túnel no establecido  
- Tráfico bloqueado  
- Comportamiento inconsistente  

---

### 15.3 Riesgos de MTU / Fragmentación

- Overhead de IPsec no considerado  
- Problemas de fragmentación  
- Fallas en PMTUD  

Impacto:

- Degradación de performance  
- Fallas intermitentes en aplicaciones  
- Troubleshooting complejo  

---

### 15.4 Riesgos de NAT

- NAT aplicado incorrectamente al tráfico VPN  
- Falta de NAT exemption  
- NAT intermedio no considerado  

Impacto:

- Fallas en establecimiento del túnel  
- Tráfico no coincidente con selectors  
- Problemas de conectividad  

---

### 15.5 Riesgos de Routing

- Rutas faltantes o incorrectas  
- Asimetría de tráfico  
- Blackholing de paquetes  

Impacto:

- Tráfico no llega al destino  
- Inestabilidad en la conectividad  

---

### 15.6 Riesgos WAN / ISP

- Alta latencia, jitter o packet loss  
- Caídas del enlace WAN  
- Variabilidad del servicio de Internet  

Impacto:

- Degradación de aplicaciones  
- Inestabilidad del túnel  
- Pérdida de conectividad  

---

### 15.7 Riesgos Multi-Vendor

- Diferencias en implementación de IPsec  
- Problemas de interoperabilidad  
- Dificultad en troubleshooting  

Impacto:

- Mayor complejidad operativa  
- Tiempo de resolución más alto  

---

### 15.8 Riesgos Operativos

- Falta de monitoreo adecuado  
- Ausencia de alertas  
- Validación incompleta post-deployment  

Impacto:

- Detección tardía de fallas  
- Mayor tiempo de recuperación  

---

### 15.9 Consideraciones de Mitigación

Para reducir los riesgos identificados, se recomienda:

- Validar parámetros antes del despliegue (pre-checks)  
- Utilizar automatización para consistencia  
- Implementar validaciones post-deployment  
- Habilitar monitoreo y alertas  
- Realizar pruebas de conectividad y failover  

---

### 15.10 Consideraciones de Diseño

- Los riesgos deben ser considerados desde el inicio del diseño  
- La automatización ayuda a reducir errores humanos  
- La validación es tan importante como la configuración  
- El diseño debe contemplar escenarios de falla  

---
# ⚙️ PART 2 — Network Implementation Plan (NIP)

## 16. Overview de Implementación

### 16.1 Objetivo

El objetivo de esta sección es describir el proceso de implementación de la VPN IPSec entre Fortigate y Palo Alto, incluyendo las validaciones previas, el despliegue de configuración y la verificación posterior.

El enfoque está orientado a garantizar una implementación controlada, repetible y con bajo riesgo operativo.

---

### 16.2 Enfoque de Automatización

La implementación se realizará utilizando **Ansible** como framework principal de automatización.

Ansible será responsable de:

- Ejecutar validaciones previas (pre-checks)  
- Aplicar la configuración en ambos dispositivos  
- Ejecutar validaciones posteriores (post-checks)  
- Realizar testing básico de conectividad  
- Generar resultados de ejecución (pass / fail)  

Se utilizarán módulos específicos de cada vendor para garantizar consistencia y manejo estructurado de la configuración.

---

### 16.3 Alcance de la Implementación

El proceso de implementación incluye:

- Configuración de parámetros de VPN (IKE / IPsec)  
- Creación de interfaces de túnel  
- Configuración de routing (baseline estático)  
- Aplicación de security policies  
- Configuración de NAT exemption  
- Commit / save de configuración  
- Validación de estado del túnel  
- Pruebas de conectividad  

---

### 16.4 Flujo General

El proceso de implementación sigue el siguiente flujo lógico:

1. Ejecución de pre-checks  
2. Aplicación de configuración en Fortigate  
3. Aplicación de configuración en Palo Alto  
4. Configuración de routing y policies  
5. Commit / save de configuración  
6. Ejecución de post-checks  
7. Testing de conectividad  

---

### 16.5 Consideraciones Operativas

- La implementación debe ser ejecutada de forma controlada  
- Se deben validar todos los parámetros antes del despliegue  
- Se debe contar con un plan de rollback  
- Se deben verificar tanto control plane como data plane  

---

### 16.6 Consideraciones de Riesgo

- Cambios en VPN pueden impactar tráfico existente  
- Errores de configuración pueden generar pérdida de conectividad  
- Se recomienda validar cada etapa antes de avanzar a la siguiente  

---

## 17. Parámetros de Entrada (Source of Truth)

### 17.1 Descripción General

La implementación se basa en un conjunto de parámetros definidos previamente, que representan el **estado deseado ** de la VPN.

Estos parámetros se utilizan como **Source of Truth** para la automatización mediante Ansible.

---

### 17.2 Formato de Datos

Los parámetros se definen en un formato estructurado (ej: YAML o JSON), lo que permite:

- Consistencia en la configuración  
- Facilidad de mantenimiento  
- Reutilización en múltiples despliegues  
- Validación previa a la ejecución  

---

### 17.3 Variables Requeridas

Los siguientes parámetros son necesarios para la implementación:

#### Información de dispositivos
- IP de gestión Fortigate  
- IP de gestión Palo Alto  
- Credenciales de acceso  

#### Conectividad WAN
- IP pública Fortigate  
- IP pública Palo Alto  

#### Redes LAN
- Subred(es) locales Fortigate  
- Subred(es) locales Palo Alto  

#### Red de túnel
- Network (/30)  
- IP de túnel en cada extremo  

#### Parámetros de IKE (Phase 1)
- Versión (IKEv2)  
- Encryption  
- Integrity  
- DH Group  
- Lifetime  
- Pre-Shared Key (PSK)  

#### Parámetros de IPsec (Phase 2)
- Encryption  
- Integrity  
- PFS  
- Lifetime  

#### Routing
- Tipo (static / BGP)  
- Redes a anunciar  

#### Políticas
- Subredes permitidas  
- Puertos / aplicaciones  

---

### 17.4 Ejemplo de Estructura (YAML)

```yaml
vpn_name: site_to_site_vpn

fortigate:
  mgmt_ip: x.x.x.x
  wan_ip: x.x.x.x
  lan_subnets:
    - 10.10.10.0/24

paloalto:
  mgmt_ip: x.x.x.x
  wan_ip: x.x.x.x
  lan_subnets:
    - 192.168.1.0/24

tunnel:
  network: 169.254.1.0/30
  fortigate_ip: 169.254.1.1/30
  paloalto_ip: 169.254.1.2/30

ike:
  version: ikev2
  encryption: aes256
  integrity: sha256
  dh_group: 14
  lifetime: 28800
  psk: <secure_value>

ipsec:
  encryption: aes256
  integrity: sha256
  pfs: group14
  lifetime: 3600

routing:
  type: static
```
---

### 17.5 Validación de Parámetros

Antes de ejecutar la automatización, se deben validar los parámetros:

- Formato correcto de IPs  
- Subredes no superpuestas  
- Coincidencia de parámetros en ambos extremos  
- Valores válidos para encryption / integrity / DH  

---

### 17.6 Consideraciones de Seguridad

- Las credenciales y PSK no deben almacenarse en texto plano  
- Se recomienda el uso de mecanismos seguros (ej: Ansible Vault)  
- Se debe restringir el acceso a los archivos de configuración  

---

### 17.7 Consideraciones de Diseño

- La separación entre datos (variables) y lógica (playbooks) mejora la mantenibilidad  
- El uso de Source of Truth permite consistencia entre despliegues  
- La validación previa reduce errores en producción  
---

## 18. VPN Parameters

### 18.1 Descripción General

En esta sección se definen los parámetros específicos de la VPN IPSec para ambos extremos (Fortigate y Palo Alto).

Estos valores deben coincidir exactamente para garantizar el correcto establecimiento del túnel.

---

### 18.2 Tabla de Parámetros

| Parameter        | Fortigate        | Palo Alto        |
|-----------------|-----------------|-----------------|
| WAN IP          | 203.0.113.10    | 198.51.100.20
| LAN Subnet      | 10.10.10.0/24   | 192.168.1.0/24  |
| Tunnel Network  | 169.254.1.0/30  | 169.254.1.0/30  |
| Tunnel IP       | 169.254.1.1/30  | 169.254.1.2/30  |
| IKE Version     | IKEv2           | IKEv2           |
| Encryption P1   | AES256          | AES256          |
| Integrity P1    | SHA256          | SHA256          |
| DH Group        | 14              | 14              |
| Lifetime P1     | 28800           | 28800           |
| Encryption P2   | AES256          | AES256          |
| Integrity P2    | SHA256          | SHA256          |
| PFS             | Group14         | Group14         |
| Lifetime P2     | 3600            | 3600            |
| PSK             | vpn_shared_key  | vpn_shared_key  |

---

### 18.3 Consideraciones

- Los parámetros de Phase 1 y Phase 2 deben coincidir en ambos extremos  
- Diferencias en valores pueden impedir el establecimiento del túnel  
- Se recomienda utilizar algoritmos seguros (AES256, SHA256, DH14 o superior)  
- La red de túnel (/30) se utiliza como red de tránsito para routing  

---

### 18.4 Consideraciones de Seguridad

- El valor de PSK mostrado es referencial  
- En entornos reales, se debe almacenar de forma segura (ej: Ansible Vault)  
- Se recomienda utilizar claves robustas y rotarlas periódicamente  

---

## 19. Automation Tools

### 19.1 Descripción General

La automatización del proceso de implementación se realiza utilizando **Ansible** como framework principal de orquestación.

El objetivo es garantizar:

- Consistencia en la configuración  
- Repetibilidad del proceso  
- Reducción de errores humanos  
- Ejecución controlada del cambio  

---

### 19.2 Ansible como Orquestador

Ansible se utiliza como herramienta central para:

- Ejecutar pre-checks  
- Aplicar configuración en ambos dispositivos  
- Gestionar el orden de ejecución  
- Ejecutar post-checks  
- Realizar testing básico de conectividad  
- Generar resultados de ejecución (pass / fail)  

Este enfoque permite manejar el deployment como un flujo estructurado.

---

### 19.3 Uso de Módulos por Vendor

Se utilizan collections oficiales de Ansible Galaxy para interactuar con cada plataforma:

- **Fortigate:**
  - Collection: `fortinet.fortios`  
  - https://galaxy.ansible.com/fortinet/fortios  

- **Palo Alto:**
  - Collection: `paloaltonetworks.panos`  
  - https://galaxy.ansible.com/paloaltonetworks/panos  

Estas collections proveen módulos específicos para cada vendor y permiten:

- Configuración estructurada  
- Manejo idempotente  
- Abstracción del CLI  
- Integración con playbooks de Ansible  


---

### 19.4 Enfoque de Integración

La automatización se basa en:

- Separación entre datos (variables) y lógica (playbooks)  
- Uso de un Source of Truth (YAML)  
- Ejecución de tareas en orden controlado  

Esto permite mantener el diseño limpio y mantenible.

---

### 19.5 Fallback Operativo

En caso de que alguna funcionalidad no esté soportada por módulos:

- Se puede utilizar acceso por CLI (SSH) como método alternativo  

Sin embargo, este enfoque se considera secundario.

---

### 19.6 Consideraciones de Diseño

- Ansible actúa como capa de orquestación única  
- Se evita el uso de múltiples mecanismos paralelos de configuración  
- La automatización está orientada a minimizar riesgo operativo  
- El enfoque permite extender la solución a múltiples despliegues  

---

### 19.7 Uso de APIs

Aunque la automatización se realiza principalmente mediante Ansible, los módulos utilizados internamente interactúan con las APIs de cada plataforma.

Esto permite realizar operaciones como:

- Consulta del estado del túnel (IKE / IPsec)  
- Verificación de configuración  
- Obtención de información de routing  
- Validación de políticas  

#### APIs por Vendor

- **Fortigate (FortiOS REST API):**
  - https://docs.fortinet.com/document/fortigate/7.2.0/secgw-for-mobile-networks-deployment/937679/monitor-vpn-apis

- **Palo Alto (PAN-OS APIs):**
  - REST API:
    - https://pan.dev/panos/docs/restapi/ 
  - XML API:
    - https://pan.dev/panos/docs/xmlapi/ 

Estas APIs permiten interacción programática directa con los dispositivos y son utilizadas de forma abstracta a través de los módulos de Ansible.

---

### 19.8 Consideraciones de Diseño (APIs)

- Ansible actúa como capa de abstracción sobre las APIs  
- El uso de APIs permite validación más precisa y estructurada  
- Facilita integración con otras herramientas (CI/CD, monitoring)  
- Permite extender la automatización más allá del deployment  

---

## 20. Automation Workflow

### 20.1 Descripción General

El proceso de automatización sigue un flujo estructurado que permite ejecutar la implementación de forma controlada, validando cada etapa antes de avanzar a la siguiente.

Este enfoque reduce el riesgo operativo y facilita la detección de errores.

---

### 20.2 Flujo de Ejecución

El workflow se compone de las siguientes etapas:

1. **Pre-Checks**
   - Validación de conectividad hacia dispositivos  
   - Validación de parámetros de entrada  
   - Verificación de estado base  

2. **Configuración en Fortigate**
   - Creación de objetos  
   - Configuración de IKE (Phase 1)  
   - Configuración de IPsec (Phase 2)  
   - Creación de tunnel interface  

3. **Configuración en Palo Alto**
   - Creación de objetos  
   - Configuración de IKE (Phase 1)  
   - Configuración de IPsec (Phase 2)  
   - Creación de tunnel interface  

4. **Configuración de Routing**
   - Definición de rutas estáticas  
   - Preparación para BGP (si aplica)  

5. **Configuración de Security Policies**
   - Permitir tráfico entre redes  
   - Habilitar logging  

6. **Configuración de NAT**
   - Aplicación de NAT exemption (no-NAT)  

7. **Commit / Save**
   - Aplicación de cambios en ambos dispositivos  

8. **Post-Checks**
   - Verificación de IKE SA  
   - Verificación de IPsec SA  
   - Validación de routing  

9. **Testing**
   - Ping entre tunnel IPs  
   - Ping entre redes LAN  
   - Traceroute  

---

### 20.3 Orden de Ejecución

El orden de ejecución es importante para evitar fallas:

- Configuración de ambos extremos antes de validar el túnel  
- Aplicación de routing y policies antes de testing  
- Validación progresiva en cada etapa  

---

### 20.4 Manejo de Errores

En caso de error:

- Se detiene la ejecución del workflow  
- Se reporta el estado de falla  
- Se evita avanzar a la siguiente etapa  

---

### 20.5 Consideraciones de Diseño

- El workflow está diseñado para ser repetible  
- Cada etapa puede ser validada de forma independiente  
- La automatización permite reducir errores humanos  
- El flujo puede extenderse para incluir validaciones adicionales  


---

## 21. Pre-Checks 

### 21.1 Descripción General

Antes de ejecutar cualquier cambio, es fundamental validar el estado actual del entorno.

Los pre-checks permiten detectar problemas potenciales antes del despliegue y reducir el riesgo de fallas durante la implementación.

---

### 21.2 Validación de Conectividad

- Verificar reachability hacia ambos dispositivos (Fortigate y Palo Alto)  
- Validar acceso a interfaces de gestión  
- Confirmar que no existen bloqueos de red intermedios  

---

### 21.3 Validación de Acceso

- Verificar credenciales de acceso (API / SSH)  
- Confirmar permisos suficientes para realizar cambios  
- Validar que Ansible puede ejecutar tareas correctamente  

---

### 21.4 Validación de Interfaces WAN

- Verificar estado de interfaces WAN (up/up)  
- Confirmar configuración de IP pública  
- Validar conectividad hacia Internet  

---

### 21.5 Validación de Parámetros de VPN

- Confirmar que los parámetros de Phase 1 y Phase 2 coinciden  
- Validar formato de IPs y subredes  
- Verificar que no existan subredes superpuestas  

---

### 21.6 Validación de Routing

- Verificar tabla de routing actual  
- Confirmar ausencia de rutas conflictivas  
- Validar conectividad base entre dispositivos  

---

### 21.7 Validación de NAT

- Verificar reglas existentes de NAT  
- Confirmar que no haya reglas que interfieran con la VPN  
- Identificar necesidad de NAT exemption  

---

### 21.8 Validación de Recursos

- Verificar uso de CPU y memoria en los dispositivos  
- Confirmar capacidad para soportar cifrado IPsec  
- Validar que no existan condiciones de saturación  

---

### 21.9 Validación de Políticas de Seguridad

- Verificar políticas existentes  
- Confirmar que no existan reglas que bloqueen el tráfico esperado  
- Identificar necesidad de nuevas políticas  

---

### 21.10 Validación de Puertos y Protocolos

- Confirmar que se permiten:
  - UDP 500 (IKE)  
  - UDP 4500 (NAT-T)  
  - ESP (si aplica)  

---

### 21.11 Consideraciones de Diseño

- Los pre-checks son obligatorios antes de cualquier cambio  
- Permiten detectar errores antes de impactar producción  
- Deben ser automatizados para consistencia  
- Reducen significativamente el riesgo operativo  

---

## 22. Deployment Plan

### 22.1 Descripción General

El deployment plan describe los pasos necesarios para implementar la VPN IPSec entre Fortigate y Palo Alto de forma controlada.

Las tareas se ejecutan de manera secuencial para garantizar consistencia y facilitar la validación en cada etapa.

---

### 22.2 Creación de Objetos

- Crear address objects para redes locales  
- Definir zonas necesarias (LAN, WAN, VPN)  
- Preparar interfaces lógicas si corresponde  

---

### 22.3 Configuración de IKE (Phase 1)

En ambos dispositivos:

- Definir peer (IP remota)  
- Configurar parámetros:
  - IKEv2  
  - Encryption (AES256)  
  - Integrity (SHA256)  
  - DH Group (14)  
  - Lifetime  
- Configurar autenticación (PSK)  

---

### 22.4 Configuración de IPsec (Phase 2)

- Definir parámetros de cifrado:
  - AES256 / SHA256  
  - PFS Group14  
  - Lifetime  
- Configurar selectors (en caso de ser requeridos)  

---

### 22.5 Creación de Tunnel Interface

- Crear interfaz lógica de túnel  
- Asignar IP correspondiente (169.254.1.x/30)  
- Asociar interfaz al túnel IPSec  

---

### 22.6 Configuración de Routing

- Configurar rutas hacia redes remotas vía interfaz de túnel  
- Verificar instalación de rutas en la tabla de routing  

---

### 22.7 Configuración de Security Policies

- Permitir tráfico entre zonas LAN ↔ VPN  
- Definir origen, destino y servicios permitidos  
- Habilitar logging  

---

### 22.8 Configuración de NAT Exemption

- Crear regla de no-NAT para tráfico entre redes locales  
- Validar orden de evaluación de reglas  

---

### 22.9 Commit / Save

- Aplicar configuración en ambos dispositivos  
- Guardar cambios  

---

### 22.10 Validación Inicial

- Verificar establecimiento del túnel  
- Confirmar estado de IKE e IPsec  
- Validar routing básico  

---

### 22.11 Consideraciones de Ejecución

- Ejecutar los cambios en ventanas controladas  
- Validar cada etapa antes de continuar  
- Evitar cambios simultáneos no controlados  
- Documentar resultados del deployment  


---

## 23. Post-Checks

### 23.1 Descripción General

Una vez finalizado el deployment, es necesario validar que la VPN IPSec se encuentra operativa y que la conectividad entre sitios funciona correctamente.

Los post-checks permiten confirmar el estado del túnel, el routing y el flujo real de tráfico.

---

### 23.2 Validación de Control Plane

Se deben verificar los siguientes elementos:

- Estado de IKE (Phase 1)  
- Estado de IPsec (Phase 2)  
- Security Associations (SA) activas  
- Eventos de negociación y rekey  

Resultado esperado:

- Túnel establecido correctamente  
- Sin errores de negociación  

---

### 23.3 Validación de Routing

- Verificar presencia de rutas hacia redes remotas  
- Confirmar instalación en la tabla de routing  
- Validar next-hop hacia la interfaz de túnel  

Resultado esperado:

- Rutas correctamente instaladas  
- Tráfico encaminado hacia el túnel  

---

### 23.4 Validación de Data Plane

- Ejecutar ping entre IPs de túnel  
- Ejecutar ping entre redes LAN  
- Ejecutar traceroute  

Resultado esperado:

- Conectividad exitosa  
- Trayectoria correcta a través del túnel  

---

### 23.5 Validación de Políticas de Seguridad

- Confirmar que las policies permiten el tráfico esperado  
- Verificar logs asociados  
- Validar contadores de tráfico  

---

### 23.6 Validación de NAT

- Confirmar que el tráfico VPN no es NATeado  
- Verificar coincidencia con reglas de NAT exemption  

---

### 23.7 Validación de Tráfico

- Verificar incremento de counters en el túnel  
- Confirmar flujo de tráfico bidireccional  

---

### 23.8 Validación de Logs

- Revisar logs de VPN  
- Identificar errores o advertencias  
- Confirmar ausencia de eventos anómalos  

---

### 23.9 Criterios de Éxito

El deployment se considera exitoso si:

- El túnel IPSec está activo  
- Las rutas están correctamente instaladas  
- Existe conectividad entre redes  
- No se detectan errores en logs  

---

### 23.10 Consideraciones de Diseño

- El estado del túnel no garantiza conectividad  
- Es necesario validar control plane y data plane  
- La validación debe ser consistente y repetible  
- Se recomienda automatizar los post-checks  
 

---

## 24. Testing Funcional

### 24.1 Descripción General

Una vez validados los aspectos básicos de conectividad, se deben realizar pruebas funcionales para asegurar que el túnel soporta correctamente el tráfico esperado.

Estas pruebas permiten validar el comportamiento del túnel en condiciones reales de uso.

---

### 24.2 Pruebas de Conectividad Básica

- Ping entre redes LAN  
- Ping entre hosts específicos  
- Verificación de conectividad bidireccional  

---

### 24.3 Pruebas de Transporte (TCP / UDP)

- Validar conectividad TCP  
- Validar tráfico UDP (si aplica)  
- Confirmar establecimiento de sesiones  

---

### 24.4 Validación de Aplicaciones

- Acceso a servicios remotos  
- Validación de aplicaciones críticas  
- Confirmación de funcionamiento esperado  

---

### 24.5 Validación de Performance Básica

- Medición básica de latencia  
- Observación de posibles pérdidas de paquetes  
- Validación de estabilidad del túnel  

---

### 24.6 Validación de Flujo de Tráfico

- Confirmar que el tráfico pasa por el túnel  
- Verificar counters en interfaces y túnel  
- Validar ausencia de rutas alternativas no deseadas  

---

### 24.7 Validación de QoS (si aplica)

- Verificar clasificación de tráfico  
- Confirmar priorización en el egress  
- Validar comportamiento bajo carga  

---

### 24.8 Escenarios de Prueba

Se recomienda probar:

- Tráfico normal  
- Tráfico bajo carga (si es posible)  
- Diferentes tipos de aplicaciones  

---

### 24.9 Criterios de Éxito

Las pruebas se consideran exitosas si:

- Las aplicaciones funcionan correctamente  
- No se observan errores en la comunicación  
- El túnel se mantiene estable durante las pruebas  

---

### 24.10 Consideraciones de Diseño

- Testing funcional valida el uso real del túnel  
- Debe ir más allá de pruebas ICMP  
- Permite detectar problemas que no aparecen en post-checks  
- Es clave para validar experiencia de usuario  


---

## 25. Validación Automatizada

### 25.1 Descripción General

La validación automatizada permite verificar el estado de la VPN de forma consistente y repetible, reduciendo la necesidad de intervención manual.

Esta validación se ejecuta mediante Ansible una vez finalizado el deployment.

---

### 25.2 Objetivos

Los objetivos principales son:

- Confirmar el estado del túnel IPSec  
- Verificar la instalación de rutas  
- Validar conectividad entre sitios  
- Detectar errores de configuración  

---

### 25.3 Validaciones Incluidas

Se realizan las siguientes verificaciones:

#### Estado del Túnel
- Verificar IKE SA (Phase 1)  
- Verificar IPsec SA (Phase 2)  

#### Routing
- Confirmar presencia de rutas hacia redes remotas  
- Validar next-hop correcto  

#### Conectividad
- Ejecutar ping entre IPs de túnel  
- Ejecutar ping entre redes LAN  

#### Políticas
- Validar existencia de security policies  
- Verificar contadores de tráfico  

#### Validación vía API
- Consulta del estado del túnel mediante APIs del dispositivo  
- Verificación de configuración aplicada  
- Validación de estado de interfaces y routing 

---

### 25.4 Resultados

Los resultados de la validación se clasifican como:

- **Pass:** todas las validaciones exitosas  
- **Fail:** una o más validaciones fallidas  

Se debe generar un output claro que permita identificar rápidamente el estado del deployment.

---

### 25.5 Manejo de Fallas

En caso de falla:

- Identificar la etapa donde ocurrió el problema  
- Registrar el error  
- Evitar avanzar con cambios adicionales  
- Evaluar necesidad de rollback  

---

### 25.6 Integración con Workflow

La validación automatizada forma parte del workflow de deployment:

- Se ejecuta inmediatamente después de los post-checks  
- Permite confirmar el estado final del sistema  

---

### 25.7 Consideraciones de Diseño

- La validación debe ser automatizada para garantizar consistencia  
- Reduce dependencia de validaciones manuales  
- Mejora la confiabilidad del deployment  
- Facilita integración con pipelines futuros (CI/CD)  
 

---

## 26. Validation and Alerting

### 26.1 Descripción General

Una vez realizada la validación automatizada, es necesario definir mecanismos de alerting para detectar y reaccionar ante fallas en la VPN.

El objetivo es asegurar una respuesta rápida frente a incidentes.

---

### 26.2 Eventos a Monitorear

Se deben generar alertas ante los siguientes eventos:

- Túnel IPSec down  
- Fallas en IKE o IPsec  
- Pérdida de rutas  
- Falta de conectividad entre sitios  
- Cambios inesperados en configuración  

---

### 26.3 Tipos de Alertas

Las alertas pueden clasificarse como:

- **Críticas:**
  - Túnel down  
  - Pérdida total de conectividad  

- **Advertencias:**
  - Degradación de performance  
  - Eventos de rekey inusuales  

---

### 26.4 Integración con Validación

Las alertas se generan en base a los resultados de la validación automatizada:

- Resultado **Fail** → alerta inmediata  
- Resultado **Pass** → estado normal  

---

### 26.5 Respuesta ante Incidentes

Ante una alerta, se deben ejecutar las siguientes acciones:

1. Identificar el tipo de falla  
2. Revisar logs y estado del túnel  
3. Validar routing y policies  
4. Determinar si es necesario ejecutar rollback  

---

### 26.6 Consideraciones de Diseño

- La validación debe estar integrada con alerting  
- Las alertas deben ser claras y accionables  
- Se debe minimizar el tiempo de detección de fallas  
- El diseño debe facilitar troubleshooting  
  

---

## 27. Rollback Plan

### 27.1 Descripción General

El rollback plan define las acciones necesarias para revertir los cambios realizados en caso de falla durante o después del deployment.

El objetivo es restaurar el estado previo del sistema y minimizar el impacto en la operación.

---

### 27.2 Escenarios de Rollback

Se debe considerar rollback en los siguientes casos:

- El túnel IPSec no se establece  
- No existe conectividad entre redes  
- Problemas de routing  
- Impacto negativo en servicios existentes  

---

### 27.3 Estrategia de Rollback

El rollback debe realizarse de forma controlada, siguiendo el orden inverso del deployment.

Pasos generales:

1. Eliminar o deshabilitar el túnel IPSec  
2. Remover configuración de Phase 1 y Phase 2  
3. Eliminar interfaz de túnel  
4. Remover rutas configuradas  
5. Eliminar o deshabilitar security policies  
6. Remover reglas de NAT exemption  
7. Restaurar configuración previa (si aplica)  

---

### 27.4 Validación del Rollback

Una vez ejecutado el rollback, se debe validar:

- Restauración de conectividad previa  
- Estado estable de los dispositivos  
- Ausencia de errores en logs  

---

### 27.5 Automatización del Rollback

El rollback puede ser automatizado mediante Ansible:

- Playbooks específicos para revertir cambios  
- Ejecución controlada en caso de fallo  
- Validación posterior automática  

---

### 27.6 Consideraciones de Diseño

- Todo cambio debe tener un plan de rollback definido  
- El rollback debe ser probado previamente cuando sea posible  
- La automatización facilita una reversión rápida y consistente  
- Se debe minimizar el tiempo de recuperación ante fallas  


---

## 28. Monitoreo y Alertas

### 28.1 Descripción General

Una vez implementada la VPN IPSec, es fundamental contar con mecanismos de monitoreo continuo para garantizar su correcto funcionamiento en el tiempo.

El monitoreo permite detectar problemas de forma temprana y mantener la estabilidad del servicio.

---

### 28.2 Elementos a Monitorear

Se deben monitorear los siguientes componentes:

#### Estado del Túnel
- Estado de IKE (Phase 1)  
- Estado de IPsec (Phase 2)  
- Número de SA activas  

#### Tráfico
- Bytes y paquetes transmitidos  
- Uso del túnel  
- Variaciones en el tráfico  

#### Routing
- Presencia de rutas hacia redes remotas  
- Estado de sesiones BGP (si aplica)  

#### Logs
- Eventos de VPN  
- Eventos de seguridad  
- Eventos de NAT  

---

### 28.3 Alertas

Se deben configurar alertas para:

- Túnel IPSec down  
- Fallas de negociación (IKE / IPsec)  
- Pérdida de rutas  
- Anomalías en tráfico  

Las alertas deben ser:

- Claras  
- Accionables  
- Prioritizadas según criticidad  

---

### 28.4 Frecuencia de Monitoreo

- Monitoreo continuo del estado del túnel  
- Validaciones periódicas de conectividad  
- Revisión de logs en caso de eventos  

---

### 28.5 Consideraciones de Diseño

- El monitoreo es clave para operación estable  
- Se debe asegurar visibilidad tanto de control plane como data plane  
- Las alertas deben permitir una rápida identificación del problema  
- El monitoreo debe integrarse con procesos operativos existentes  