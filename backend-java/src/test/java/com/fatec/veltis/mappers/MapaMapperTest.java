package com.fatec.veltis.mappers;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNull;

import org.junit.jupiter.api.Test;

class MapaMapperTest {

    @Test
    void formataCep() {
        assertEquals("18013-280", MapaMapper.formatarCep("18013280"));
        assertNull(MapaMapper.formatarCep("123"));
        assertNull(MapaMapper.formatarCep(null));
    }
}
