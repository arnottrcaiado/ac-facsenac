/*
    FACULDADE SENAC PE

    Automação Comercial

    Autor: Prof. Arnott Ramos Caiado

    Exemplo de envio de medida ( temperatura ) para APIs HTTP
    versao com uso de ID e KEY

    Hardware

    NODEMCU ESP8266
    Sensor Temperatura e Umidade - DHT 22 ou DHT11


*/
#include <ESP8266WiFi.h>        /* bilblioteca adequada para wifi esp8266 */
#include <ESP8266HTTPClient.h>  /* biblioteca para acesso à API */
#include "DHT.h"                /* bib sensor dht */

#define api_header_key  "ueyr123768565HGHgjhgHGHJghjghgHDFgdfdhgfklkjlkjuytty68"

#define DHTPIN 5      // pino D1 do nodemcu
#define DHTTYPE 11    // especificacao do modelo de sensor DHT
#define http_app "http://fac.pythonanywhere.com/datalog"  // url da API



#define IDMODULO "A11"  // definição da identificação do modulo de leitura e placa
#define KEYAPI "1A2b3C4E5f"       // definição da chave de segurança - deve ser criptografada e sofrer mudanças temporárias

#define REDEWIFI   "VIVOFIBRA-3AF0"     // wifi a ser utilizada
#define SENHA       "AAAAC0A537"        // senha da rede wifi a ser utilizada

/*
 * Variáveis globais
 */
unsigned long intervalo = 60000;  // variavel para definir intervalo entre leituras - cada 1000 equivale a um segundo
unsigned long tempoAnterior = 0;  // variavel para guardar o momento da leitura / envio anterior
int num_medida = 0;

int temp_anterior=0;  // temperatura anterior
int temp_atual=0;     // temperatura atual
int status_mudanca=0;   // variavel para registrar midanca 0=nao, 1=sim

DHT dht(DHTPIN, DHTTYPE); /* configura o pino e o tipo de sensor utilizado */

/*
   Inicialização / SETUP
   neste caso, conexao a rede wifi disponivel
*/
void setup () {

  Serial.begin(115200);
  WiFi.begin( REDEWIFI , SENHA );
  dht.begin();

  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.print("Connectando à rede WIFI..:");
    Serial.println(REDEWIFI);
  }
  Serial.print("Connectado à rede WIFI ");
  Serial.println(REDEWIFI);
}

void loop() {
  String endpoint;
  char medida[10];
  static float temperatura, umidade;
  unsigned long tempoatual = millis();

  if ( (tempoatual - tempoAnterior) > intervalo )
  {
    tempoAnterior = tempoatual;

    if (WiFi.status() == WL_CONNECTED) { // Verificando o status da conexão WiFi

      HTTPClient http;  // Declaração de objeto da classe HTTPClient

      num_medida++;
      temperatura = dht.readTemperature();
      umidade = dht.readHumidity();
      temp_atual=int(temperatura);



      if ( isnan( temperatura ) || isnan ( umidade ) )  /* funcao paraa testar se a leitura foi bem sucedida */
      {
        Serial.println( "Erro na medicao\n" );
        delay(100);
      }
      else
      {
        if ( temp_atual != temp_anterior ) {
          temp_anterior = temp_atual;
          status_mudanca=1;
        } else {
          status_mudanca=0;
        }
        env_Dados( temperatura, umidade, status_mudanca, http_app, IDMODULO, KEYAPI );

      }
    }
  }
}

/*
 * Função para preparar e realização uma requisição HTTP com informações de temperatura
 *
 * Http da api
 * identificação do sensor
 * chave do modulo para testar segurança
 */
void env_Dados ( float temperatura, float umidade, int stat_mudancas, char *http_api , char *id_api, char*chave_modulo) {
  String endpoint;
  char temp[4];
  char umidad[4];
  char stat[3];
  HTTPClient http;  // Declarar  um objeto da classe HTTPClient

  Serial.println( http_api );
  http.begin( http_api ); // Especificando o endereço da requisição HTTP
  http.addHeader("Content-Type","application/x-www-form-urlencoded");
  http.addHeader("Authorization-Token", api_header_key );

  sprintf( temp, "%2d", (int)temperatura );
  sprintf( stat, "%1d", (int)stat_mudancas );
  sprintf( umidad, "%2d", (int)umidade );

  endpoint = "api_key=";
  endpoint += chave_modulo;
  endpoint += "&id=";
  endpoint += id_api;
  endpoint += "&chave=";
  endpoint += chave_modulo;
  endpoint += "&medida=";
  endpoint += temp;
  endpoint += "&umidade=";
  endpoint += umidad;
  endpoint += "&status=";
  endpoint += stat;

  int httpCode = http.POST(endpoint); // Enviando a requisição

  if (httpCode > 0) {                           // Verificando o retorno da requisição
    String retorno = http.getString();    // obtendo o retorno da requisição
    Serial.println( retorno );            // mostrando o retorno
  }
  else {
    Serial.print("Erro na requisição:");
    Serial.println( http_api );
  }
  http.end();   //Close connection
}
