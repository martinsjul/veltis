package com.fatec.veltis.exceptions;

import java.time.LocalDateTime;
import java.util.List;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.dao.InvalidDataAccessApiUsageException;
import org.springframework.data.core.PropertyReferenceException;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.http.converter.HttpMessageNotReadableException;
import org.springframework.web.HttpMediaTypeNotSupportedException;
import org.springframework.web.HttpRequestMethodNotSupportedException;
import org.springframework.web.bind.MissingServletRequestParameterException;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.method.annotation.HandlerMethodValidationException;
import org.springframework.web.method.annotation.MethodArgumentTypeMismatchException;
import org.springframework.web.servlet.resource.NoResourceFoundException;

import com.fatec.veltis.dtos.ErroResponse;
import com.fatec.veltis.dtos.ErroResponse.CampoInvalido;

import jakarta.servlet.http.HttpServletRequest;

/**
 * Transforma as exceções em respostas JSON com o status HTTP certo.
 * Assim os controllers e services não precisam montar respostas de erro.
 */
@RestControllerAdvice
public class TratadorDeErros {

    private static final Logger log = LoggerFactory.getLogger(TratadorDeErros.class);

    /** 400: o JSON de entrada não passou nas anotações do DTO (@NotBlank, @Pattern...). */
    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ErroResponse> corpoInvalido(MethodArgumentNotValidException ex, HttpServletRequest req) {
        List<CampoInvalido> campos = ex.getBindingResult().getFieldErrors().stream()
                .map(f -> new CampoInvalido(f.getField(), f.getDefaultMessage()))
                .toList();
        return resposta(HttpStatus.BAD_REQUEST, "Dados inválidos. Corrija os campos indicados.", req, campos);
    }

    /** 400: parâmetro da URL inválido (ex.: ?municipio=abc com @Pattern). */
    @ExceptionHandler(HandlerMethodValidationException.class)
    public ResponseEntity<ErroResponse> parametroInvalido(HandlerMethodValidationException ex, HttpServletRequest req) {
        List<CampoInvalido> campos = ex.getParameterValidationResults().stream()
                .flatMap(r -> r.getResolvableErrors().stream()
                        .map(e -> new CampoInvalido(r.getMethodParameter().getParameterName(), e.getDefaultMessage())))
                .toList();
        return resposta(HttpStatus.BAD_REQUEST, "Parâmetros inválidos.", req, campos);
    }

    /** 400: tipo errado na URL (ex.: /escolas/abc ou ?dependencia=PARTICULAR). */
    @ExceptionHandler(MethodArgumentTypeMismatchException.class)
    public ResponseEntity<ErroResponse> tipoErrado(MethodArgumentTypeMismatchException ex, HttpServletRequest req) {
        String msg = "Valor '" + ex.getValue() + "' inválido para '" + ex.getName() + "'.";
        return resposta(HttpStatus.BAD_REQUEST, msg, req, List.of(new CampoInvalido(ex.getName(), msg)));
    }

    /** 400: JSON mal formado ou enum com valor que não existe (ex.: "rede": "MISTA"). */
    @ExceptionHandler(HttpMessageNotReadableException.class)
    public ResponseEntity<ErroResponse> jsonIlegivel(HttpMessageNotReadableException ex, HttpServletRequest req) {
        return resposta(HttpStatus.BAD_REQUEST,
                "O corpo da requisição não é um JSON válido ou tem um valor não aceito.", req, List.of());
    }

    /** 400: ordenação por um campo que não existe (ex.: ?sort=cor). */
    @ExceptionHandler({PropertyReferenceException.class, InvalidDataAccessApiUsageException.class})
    public ResponseEntity<ErroResponse> ordenacaoInvalida(Exception ex, HttpServletRequest req) {
        return resposta(HttpStatus.BAD_REQUEST,
                "Parâmetro de consulta inválido. Confira o campo usado em ?sort= (ex.: sort=nome).", req,
                List.of(new CampoInvalido("sort", "campo inexistente")));
    }

    @ExceptionHandler(RequisicaoInvalidaException.class)
    public ResponseEntity<ErroResponse> requisicaoInvalida(RequisicaoInvalidaException ex, HttpServletRequest req) {
        return resposta(HttpStatus.BAD_REQUEST, ex.getMessage(), req, List.of());
    }

    /** 404: registro não existe. */
    @ExceptionHandler(RecursoNaoEncontradoException.class)
    public ResponseEntity<ErroResponse> naoEncontrado(RecursoNaoEncontradoException ex, HttpServletRequest req) {
        return resposta(HttpStatus.NOT_FOUND, ex.getMessage(), req, List.of());
    }

    /** 404: endereço que não existe na API. */
    @ExceptionHandler(NoResourceFoundException.class)
    public ResponseEntity<ErroResponse> enderecoInexistente(NoResourceFoundException ex, HttpServletRequest req) {
        return resposta(HttpStatus.NOT_FOUND, "Endereço não encontrado na API.", req, List.of());
    }

    /** 409: regra de negócio (código repetido, apagar algo que tem dependentes...). */
    @ExceptionHandler(RegraDeNegocioException.class)
    public ResponseEntity<ErroResponse> regraDeNegocio(RegraDeNegocioException ex, HttpServletRequest req) {
        return resposta(HttpStatus.CONFLICT, ex.getMessage(), req, List.of());
    }

    /** 409: o próprio banco recusou (chave estrangeira ou chave única). */
    @ExceptionHandler(DataIntegrityViolationException.class)
    public ResponseEntity<ErroResponse> integridade(DataIntegrityViolationException ex, HttpServletRequest req) {
        log.warn("Integridade violada em {}: {}", req.getRequestURI(), ex.getMostSpecificCause().getMessage());
        return resposta(HttpStatus.CONFLICT,
                "A operação viola a integridade dos dados (registro repetido ou ainda em uso).", req, List.of());
    }

    /** 405: método HTTP que o endereço não aceita (ex.: DELETE em /mapa/instituicoes). */
    @ExceptionHandler(HttpRequestMethodNotSupportedException.class)
    public ResponseEntity<ErroResponse> metodoNaoPermitido(HttpRequestMethodNotSupportedException ex,
                                                           HttpServletRequest req) {
        return resposta(HttpStatus.METHOD_NOT_ALLOWED,
                "Método " + ex.getMethod() + " não é aceito neste endereço.", req, List.of());
    }

    /** 415: corpo enviado sem Content-Type: application/json. */
    @ExceptionHandler(HttpMediaTypeNotSupportedException.class)
    public ResponseEntity<ErroResponse> tipoDeConteudo(HttpMediaTypeNotSupportedException ex, HttpServletRequest req) {
        return resposta(HttpStatus.UNSUPPORTED_MEDIA_TYPE,
                "Envie o corpo como JSON (Content-Type: application/json).", req, List.of());
    }

    /** 400: faltou um parâmetro obrigatório na URL. */
    @ExceptionHandler(MissingServletRequestParameterException.class)
    public ResponseEntity<ErroResponse> parametroFaltando(MissingServletRequestParameterException ex,
                                                          HttpServletRequest req) {
        return resposta(HttpStatus.BAD_REQUEST, "Parâmetro obrigatório ausente: " + ex.getParameterName() + ".",
                req, List.of(new CampoInvalido(ex.getParameterName(), "obrigatório")));
    }

    /** 500: erro inesperado. O detalhe vai para o log, não para o usuário. */
    @ExceptionHandler(Exception.class)
    public ResponseEntity<ErroResponse> inesperado(Exception ex, HttpServletRequest req) {
        log.error("Erro inesperado em {}", req.getRequestURI(), ex);
        return resposta(HttpStatus.INTERNAL_SERVER_ERROR, "Erro interno. Tente de novo.", req, List.of());
    }

    private ResponseEntity<ErroResponse> resposta(HttpStatus status, String mensagem, HttpServletRequest req,
                                                  List<CampoInvalido> campos) {
        ErroResponse corpo = new ErroResponse(LocalDateTime.now(), status.value(), status.getReasonPhrase(),
                mensagem, req.getRequestURI(), campos);
        return ResponseEntity.status(status).body(corpo);
    }
}
