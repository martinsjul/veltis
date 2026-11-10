package com.fatec.veltis.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Configuration;
import org.springframework.core.convert.converter.Converter;
import org.springframework.core.convert.converter.ConverterFactory;
import org.springframework.format.FormatterRegistry;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

@Configuration
public class WebConfig implements WebMvcConfigurer {

    @Value("${veltis.cors.origens}")
    private String[] origens;

    /** Libera o frontend (React/Vite em localhost:5173) para chamar a API pelo navegador. */
    @Override
    public void addCorsMappings(CorsRegistry registry) {
        registry.addMapping("/**")
                .allowedOrigins(origens)
                .allowedMethods("GET", "POST", "PUT", "DELETE");
    }

    /** Aceita enums na URL sem diferenciar maiúsculas: ?tipo=etec e ?tipo=ETEC funcionam igual. */
    @Override
    public void addFormatters(FormatterRegistry registry) {
        registry.addConverterFactory(new EnumSemCaixa());
    }

    @SuppressWarnings({"rawtypes", "unchecked"})
    private static final class EnumSemCaixa implements ConverterFactory<String, Enum> {
        @Override
        public <T extends Enum> Converter<String, T> getConverter(Class<T> tipo) {
            return texto -> (T) Enum.valueOf(tipo, texto.trim().toUpperCase());
        }
    }
}
