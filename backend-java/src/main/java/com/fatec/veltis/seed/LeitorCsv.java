package com.fatec.veltis.seed;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.springframework.core.io.ClassPathResource;

/**
 * Lê os arquivos CSV de src/main/resources/seed (separador ";", primeira linha = cabeçalho).
 * Entende campos entre aspas, que podem ter ";" dentro.
 */
public final class LeitorCsv {

    private LeitorCsv() {
    }

    /** Cada linha vira um Map coluna -> valor (texto vazio vira null). */
    public static List<Map<String, String>> ler(String arquivo) {
        ClassPathResource recurso = new ClassPathResource("seed/" + arquivo);
        try (BufferedReader leitor = new BufferedReader(
                new InputStreamReader(recurso.getInputStream(), StandardCharsets.UTF_8))) {
            List<String> cabecalho = separar(leitor.readLine());
            List<Map<String, String>> linhas = new ArrayList<>();
            String linha;
            while ((linha = leitor.readLine()) != null) {
                if (linha.isBlank()) {
                    continue;
                }
                List<String> valores = separar(linha);
                Map<String, String> registro = new HashMap<>();
                for (int i = 0; i < cabecalho.size(); i++) {
                    String valor = i < valores.size() ? valores.get(i) : "";
                    registro.put(cabecalho.get(i), valor.isEmpty() ? null : valor);
                }
                linhas.add(registro);
            }
            return linhas;
        } catch (IOException e) {
            throw new IllegalStateException("Não foi possível ler seed/" + arquivo, e);
        }
    }

    static List<String> separar(String linha) {
        List<String> campos = new ArrayList<>();
        StringBuilder atual = new StringBuilder();
        boolean entreAspas = false;
        for (int i = 0; i < linha.length(); i++) {
            char c = linha.charAt(i);
            if (c == '"') {
                if (entreAspas && i + 1 < linha.length() && linha.charAt(i + 1) == '"') {
                    atual.append('"'); // "" dentro de aspas = uma aspa
                    i++;
                } else {
                    entreAspas = !entreAspas;
                }
            } else if (c == ';' && !entreAspas) {
                campos.add(atual.toString());
                atual.setLength(0);
            } else {
                atual.append(c);
            }
        }
        campos.add(atual.toString());
        return campos;
    }
}
