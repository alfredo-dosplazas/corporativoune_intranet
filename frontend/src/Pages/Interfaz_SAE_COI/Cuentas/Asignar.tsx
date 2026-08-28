import React, {useState} from "react";
import {useForm} from "@inertiajs/react";
import {AppLayout} from "@/layouts/AppLayout.tsx";
import {getUrl} from "@/utils/routes.ts";

interface Cuenta {
    id: number;
    nombre: string;
    numero_cuenta_coi: string;
}

type Props = {
    cuentas: Cuenta[];
};

export default function Asignar({cuentas}: Props) {
    const [idEditar, setIdEditar] = useState<number | null>(null);

    // Inicializamos el formulario de Inertia incluyendo 'id'
    const {data, setData, post, processing, errors, reset, clearErrors} = useForm({
        id: null as number | null,
        nombre: "",
        numero_cuenta_coi: "",
    });

    // Cargar los datos de la cuenta a editar en el formulario
    const handleEditar = (cuenta: Cuenta) => {
        setIdEditar(cuenta.id);
        setData({
            id: cuenta.id,
            nombre: cuenta.nombre,
            numero_cuenta_coi: cuenta.numero_cuenta_coi,
        });
        clearErrors();
    };

    // Resetear el formulario al modo creación
    const handleCancelar = () => {
        setIdEditar(null);
        reset();
        clearErrors();
    };

    // Envío del formulario siempre a la misma URL vía POST
    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();

        // Se envía a la misma ruta definida en tu url.py ('/cuentas/asignar/')
        post(getUrl('interfaz_sae_coi:asignar_cuentas'), {
            onSuccess: () => {
                handleCancelar();
            },
        });
    };

    return (
        <AppLayout>
            <div style={{maxWidth: "800px", margin: "0 auto", padding: "20px"}}>
                <h1>Gestión de Cuentas</h1>

                {/* Formulario manejado por Inertia */}
                <form
                    onSubmit={handleSubmit}
                    style={{marginBottom: "30px", background: "#f5f5f5", padding: "20px", borderRadius: "8px"}}
                >
                    <h3>{idEditar ? "Actualizar Cuenta" : "Crear Nueva Cuenta"}</h3>

                    <div style={{marginBottom: "12px"}}>
                        <label style={{display: "block", marginBottom: "4px"}}>Nombre de la Cuenta:</label>
                        <input
                            type="text"
                            value={data.nombre}
                            onChange={(e) => setData("nombre", e.target.value)}
                            placeholder="Ej. Cuenta de Clientes Cortazar"
                            required
                            style={{width: "100%", padding: "8px"}}
                        />
                        {errors.nombre && <span style={{color: "red", fontSize: "12px"}}>{errors.nombre}</span>}
                    </div>

                    <div style={{marginBottom: "12px"}}>
                        <label style={{display: "block", marginBottom: "4px"}}>Número de Cuenta COI:</label>
                        <input
                            type="text"
                            value={data.numero_cuenta_coi}
                            onChange={(e) => setData("numero_cuenta_coi", e.target.value)}
                            placeholder="Ej. 1110-001-000"
                            required
                            style={{width: "100%", padding: "8px"}}
                        />
                        {errors.numero_cuenta_coi && (
                            <span style={{color: "red", fontSize: "12px"}}>{errors.numero_cuenta_coi}</span>
                        )}
                    </div>

                    <div style={{display: "flex", gap: "10px"}}>
                        <button type="submit" disabled={processing} style={{padding: "8px 16px", cursor: "pointer"}}>
                            {processing ? "Guardando..." : idEditar ? "Guardar Cambios" : "Agregar Cuenta"}
                        </button>

                        {idEditar && (
                            <button
                                type="button"
                                onClick={handleCancelar}
                                disabled={processing}
                                style={{padding: "8px 16px", cursor: "pointer"}}
                            >
                                Cancelar
                            </button>
                        )}
                    </div>
                </form>

                {/* Tabla de Cuentas Registradas */}
                <h3>Cuentas Registradas</h3>
                <table style={{width: "100%", borderCollapse: "collapse"}}>
                    <thead>
                    <tr style={{background: "#e0e0e0", textAlign: "left"}}>
                        <th style={{padding: "8px", border: "1px solid #ccc"}}>Nombre</th>
                        <th style={{padding: "8px", border: "1px solid #ccc"}}>Nº Cuenta COI</th>
                        <th style={{padding: "8px", border: "1px solid #ccc", width: "100px"}}>Acción</th>
                    </tr>
                    </thead>
                    <tbody>
                    {cuentas.map((cuenta) => (
                        <tr key={cuenta.id}>
                            <td style={{padding: "8px", border: "1px solid #ccc"}}>{cuenta.nombre}</td>
                            <td style={{padding: "8px", border: "1px solid #ccc"}}>{cuenta.numero_cuenta_coi}</td>
                            <td style={{padding: "8px", border: "1px solid #ccc", textAlign: "center"}}>
                                <button onClick={() => handleEditar(cuenta)}>Editar</button>
                            </td>
                        </tr>
                    ))}
                    {cuentas.length === 0 && (
                        <tr>
                            <td colSpan={3} style={{textAlign: "center", padding: "12px"}}>
                                No hay cuentas registradas.
                            </td>
                        </tr>
                    )}
                    </tbody>
                </table>
            </div>
        </AppLayout>
    );
}