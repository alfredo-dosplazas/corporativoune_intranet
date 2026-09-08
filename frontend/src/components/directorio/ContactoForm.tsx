import React, {useState, useMemo, useEffect} from 'react';
import {useForm, Link} from '@inertiajs/react';
import {getUrl} from "@/utils/routes";
import type {ContactoType} from "@/types/directorio.ts";

type EmpresaOption = { id: number; nombre: string; };
type AreaOption = { id: number; nombre: string; empresa_id: number; };
type PuestoOption = { id: number; nombre: string; empresa_id?: number; };
type SedeOption = { id: number; nombre: string; };
type ContactoOption = { id: number; nombre_completo: string; };

type Props = {
    contacto?: ContactoType;
    empresas: EmpresaOption[];
    areas: AreaOption[];
    puestos: PuestoOption[];
    sedes: SedeOption[];
    contactosJefes: ContactoOption[];
    cancelUrl: string;
};

export default function ContactoForm({
                                         contacto,
                                         empresas,
                                         areas,
                                         puestos,
                                         sedes,
                                         contactosJefes,
                                         cancelUrl
                                     }: Props) {
    const [activeTab, setActiveTab] = useState<'personal' | 'laboral' | 'contacto' | 'config'>('personal');

    const {data, setData, post, processing, errors} = useForm({
        primer_nombre: contacto?.primer_nombre || '',
        segundo_nombre: contacto?.segundo_nombre || '',
        primer_apellido: contacto?.primer_apellido || '',
        segundo_apellido: contacto?.segundo_apellido || '',
        abreviatura_titulo: contacto?.abreviatura_titulo || '',
        numero_empleado: contacto?.numero_empleado || '',
        fecha_nacimiento: contacto?.fecha_nacimiento || '',
        foto: null as File | null,

        empresa_id: contacto?.empresa?.id || (empresas[0]?.id || ''),
        area_id: contacto?.area_id || '',
        puesto_id: contacto?.puesto_id || '',
        sede_administrativa_id: contacto?.sede_administrativa_id || '',
        jefe_directo_id: contacto?.jefe_directo_id || '',
        empresas_relacionadas: contacto?.empresas_relacionadas?.map((e: any) => e.id) || [],
        sedes_visibles: contacto?.sedes_visibles?.map((s: any) => s.id) || [],

        fecha_ingreso: contacto?.fecha_ingreso || '',
        fecha_egreso: contacto?.fecha_egreso || '',

        emails: contacto?.emails || [{email: '', es_principal: true, es_slack: false}],
        telefonos: contacto?.telefonos || [{telefono: '', extension: '', es_principal: true, es_celular: true}],

        mostrar_en_directorio: contacto?.mostrar_en_directorio ?? true,
        mostrar_en_cumpleanios: contacto?.mostrar_en_cumpleanios ?? true,
        es_jefe: contacto?.es_jefe ?? false,
    });

    const areasFiltradas = useMemo(() => {
        if (!data.empresa_id) return [];
        return areas.filter(a => Number(a.empresa_id) === Number(data.empresa_id));
    }, [data.empresa_id, areas]);

    const puestosFiltrados = useMemo(() => {
        if (!data.empresa_id) return [];
        return puestos.filter(p => !p.empresa_id || Number(p.empresa_id) === Number(data.empresa_id));
    }, [data.empresa_id, puestos]);

    useEffect(() => {
        if (data.area_id) {
            const areaValida = areasFiltradas.some(a => Number(a.id) === Number(data.area_id));
            if (!areaValida) {
                setData('area_id', '');
            }
        }
    }, [data.empresa_id]);

    const addEmailRow = () => {
        setData('emails', [...data.emails, {email: '', es_principal: false, es_slack: false}]);
    };

    const removeEmailRow = (index: number) => {
        setData('emails', data.emails.filter((_: any, i: number) => i !== index));
    };

    const handleEmailChange = (index: number, field: string, value: any) => {
        const newEmails = [...data.emails];
        newEmails[index][field] = value;
        if (field === 'es_principal' && value === true) {
            newEmails.forEach((e, i) => {
                if (i !== index) e.es_principal = false;
            });
        }
        setData('emails', newEmails);
    };

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (contacto?.id) {
            post(getUrl('directorio:update', contacto.id), {preserveScroll: true});
        } else {
            post(getUrl('directorio:create'), {preserveScroll: true});
        }
    };

    return (
        <form onSubmit={handleSubmit} className="space-y-6">
            <div className="bg-base-100 p-2 rounded-2xl border border-base-200 shadow-sm">
                <div className="flex gap-2 border-b border-base-200 pb-2 overflow-x-auto">
                    <button
                        type="button"
                        onClick={() => setActiveTab('personal')}
                        className={`btn btn-sm ${activeTab === 'personal' ? 'btn-primary' : 'btn-ghost'}`}
                    >
                        <span className="icon-[lucide--user] text-base"></span> Datos Personales
                    </button>
                    <button
                        type="button"
                        onClick={() => setActiveTab('laboral')}
                        className={`btn btn-sm ${activeTab === 'laboral' ? 'btn-primary' : 'btn-ghost'}`}
                    >
                        <span className="icon-[lucide--building-2] text-base"></span> Adscripción y Puesto
                    </button>
                    <button
                        type="button"
                        onClick={() => setActiveTab('contacto')}
                        className={`btn btn-sm ${activeTab === 'contacto' ? 'btn-primary' : 'btn-ghost'}`}
                    >
                        <span className="icon-[lucide--mail] text-base"></span> Contacto
                    </button>
                    <button
                        type="button"
                        onClick={() => setActiveTab('config')}
                        className={`btn btn-sm ${activeTab === 'config' ? 'btn-primary' : 'btn-ghost'}`}
                    >
                        <span className="icon-[lucide--settings] text-base"></span> Configuración
                    </button>
                </div>

                <div className="p-4 pt-6">
                    {activeTab === 'personal' && (
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                            <div className="form-control">
                                <label className="label text-xs font-semibold">Título (Abrev.)</label>
                                <input
                                    type="text"
                                    value={data.abreviatura_titulo}
                                    onChange={e => setData('abreviatura_titulo', e.target.value)}
                                    className={`input input-bordered input-sm ${errors.abreviatura_titulo ? 'input-error' : ''}`}
                                />
                                {errors.abreviatura_titulo &&
                                    <span className="text-xs text-error mt-1">{errors.abreviatura_titulo}</span>}
                            </div>

                            <div className="form-control">
                                <label className="label text-xs font-semibold">No. Empleado</label>
                                <input
                                    type="text"
                                    value={data.numero_empleado}
                                    onChange={e => setData('numero_empleado', e.target.value)}
                                    className={`input input-bordered input-sm font-mono ${errors.numero_empleado ? 'input-error' : ''}`}
                                />
                                {errors.numero_empleado &&
                                    <span className="text-xs text-error mt-1">{errors.numero_empleado}</span>}
                            </div>

                            <div className="form-control">
                                <label className="label text-xs font-semibold">Fecha de Nacimiento</label>
                                <input
                                    type="date"
                                    value={data.fecha_nacimiento}
                                    onChange={e => setData('fecha_nacimiento', e.target.value)}
                                    className={`input input-bordered input-sm ${errors.fecha_nacimiento ? 'input-error' : ''}`}
                                />
                                {errors.fecha_nacimiento &&
                                    <span className="text-xs text-error mt-1">{errors.fecha_nacimiento}</span>}
                            </div>

                            <div className="form-control">
                                <label className="label text-xs font-semibold">Primer Nombre *</label>
                                <input
                                    type="text"
                                    value={data.primer_nombre}
                                    onChange={e => setData('primer_nombre', e.target.value)}
                                    className={`input input-bordered input-sm ${errors.primer_nombre ? 'input-error' : ''}`}
                                />
                                {errors.primer_nombre &&
                                    <span className="text-xs text-error mt-1">{errors.primer_nombre}</span>}
                            </div>

                            <div className="form-control">
                                <label className="label text-xs font-semibold">Segundo Nombre</label>
                                <input
                                    type="text"
                                    value={data.segundo_nombre}
                                    onChange={e => setData('segundo_nombre', e.target.value)}
                                    className={`input input-bordered input-sm ${errors.segundo_nombre ? 'input-error' : ''}`}
                                />
                                {errors.segundo_nombre &&
                                    <span className="text-xs text-error mt-1">{errors.segundo_nombre}</span>}
                            </div>

                            <div className="form-control">
                                <label className="label text-xs font-semibold">Primer Apellido *</label>
                                <input
                                    type="text"
                                    value={data.primer_apellido}
                                    onChange={e => setData('primer_apellido', e.target.value)}
                                    className={`input input-bordered input-sm ${errors.primer_apellido ? 'input-error' : ''}`}
                                />
                                {errors.primer_apellido &&
                                    <span className="text-xs text-error mt-1">{errors.primer_apellido}</span>}
                            </div>

                            <div className="form-control">
                                <label className="label text-xs font-semibold">Segundo Apellido</label>
                                <input
                                    type="text"
                                    value={data.segundo_apellido}
                                    onChange={e => setData('segundo_apellido', e.target.value)}
                                    className={`input input-bordered input-sm ${errors.segundo_apellido ? 'input-error' : ''}`}
                                />
                                {errors.segundo_apellido &&
                                    <span className="text-xs text-error mt-1">{errors.segundo_apellido}</span>}
                            </div>
                        </div>
                    )}

                    {activeTab === 'laboral' && (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div
                                className="form-control md:col-span-2 bg-base-200/50 p-4 rounded-xl border border-base-200">
                                <label className="label text-xs font-bold text-primary">Empresa Principal (Nómina)
                                    *</label>
                                <select
                                    value={data.empresa}
                                    onChange={e => setData('empresa', e.target.value)}
                                    className={`select select-bordered select-sm w-full ${errors.empresa ? 'select-error' : ''}`}
                                >
                                    {empresas.map(emp => (
                                        <option key={emp.id} value={emp.id}>{emp.nombre}</option>
                                    ))}
                                </select>
                                {errors.empresa && <span className="text-xs text-error mt-1">{errors.empresa}</span>}
                            </div>

                            <div className="form-control">
                                <label className="label text-xs font-semibold">Área / Departamento</label>
                                <select
                                    value={data.area_id}
                                    onChange={e => setData('area_id', e.target.value)}
                                    className={`select select-bordered select-sm ${errors.area ? 'select-error' : ''}`}
                                >
                                    <option value="">-- Selecciona un área --</option>
                                    {areasFiltradas.map(area => (
                                        <option key={area.id} value={area.id}>{area.nombre}</option>
                                    ))}
                                </select>
                                {errors.area && <span className="text-xs text-error mt-1">{errors.area}</span>}
                            </div>

                            <div className="form-control">
                                <label className="label text-xs font-semibold">Puesto</label>
                                <select
                                    value={data.puesto_id}
                                    onChange={e => setData('puesto_id', e.target.value)}
                                    className={`select select-bordered select-sm ${errors.puesto ? 'select-error' : ''}`}
                                >
                                    <option value="">-- Selecciona un puesto --</option>
                                    {puestosFiltrados.map(puesto => (
                                        <option key={puesto.id} value={puesto.id}>{puesto.nombre}</option>
                                    ))}
                                </select>
                                {errors.puesto && <span className="text-xs text-error mt-1">{errors.puesto}</span>}
                            </div>

                            <div className="form-control">
                                <label className="label text-xs font-semibold">Sede Administrativa *</label>
                                <select
                                    value={data.sede_administrativa_id}
                                    onChange={e => setData('sede_administrativa_id', e.target.value)}
                                    className={`select select-bordered select-sm ${errors.sede_administrativa ? 'select-error' : ''}`}
                                >
                                    <option value="">-- Selecciona sede --</option>
                                    {sedes.map(sede => (
                                        <option key={sede.id} value={sede.id}>{sede.nombre}</option>
                                    ))}
                                </select>
                                {errors.sede_administrativa &&
                                    <span className="text-xs text-error mt-1">{errors.sede_administrativa}</span>}
                            </div>

                            <div className="form-control">
                                <label className="label text-xs font-semibold">Jefe Directo</label>
                                <select
                                    value={data.jefe_directo_id}
                                    onChange={e => setData('jefe_directo_id', e.target.value)}
                                    className="select select-bordered select-sm"
                                >
                                    <option value="">Sin jefe asignado</option>
                                    {contactosJefes.map(jefe => (
                                        <option key={jefe.id} value={jefe.id}>{jefe.nombre_completo}</option>
                                    ))}
                                </select>
                            </div>

                            <div className="form-control">
                                <label className="label text-xs font-semibold">Fecha de Ingreso</label>
                                <input
                                    type="date"
                                    value={data.fecha_ingreso}
                                    onChange={e => setData('fecha_ingreso', e.target.value)}
                                    className={`input input-bordered input-sm ${errors.fecha_ingreso ? 'input-error' : ''}`}
                                />
                                {errors.fecha_ingreso &&
                                    <span className="text-xs text-error mt-1">{errors.fecha_ingreso}</span>}
                            </div>

                            <div className="form-control">
                                <label className="label text-xs font-semibold">Fecha de Egreso</label>
                                <input
                                    type="date"
                                    value={data.fecha_egreso}
                                    onChange={e => setData('fecha_egreso', e.target.value)}
                                    className={`input input-bordered input-sm ${errors.fecha_egreso ? 'input-error' : ''}`}
                                />
                                {errors.fecha_egreso &&
                                    <span className="text-xs text-error mt-1">{errors.fecha_egreso}</span>}
                            </div>
                        </div>
                    )}

                    {activeTab === 'contacto' && (
                        <div className="space-y-4">
                            <div className="flex items-center justify-between border-b border-base-200 pb-2">
                                <h3 className="text-sm font-bold">Correos Electrónicos</h3>
                                <button type="button" onClick={addEmailRow}
                                        className="btn btn-xs btn-outline btn-primary gap-1">
                                    <span className="icon-[lucide--plus] text-xs"></span> Agregar Correo
                                </button>
                            </div>

                            {data.emails.map((row: any, idx: number) => (
                                <div key={idx}
                                     className="flex flex-col gap-1 bg-base-200/40 p-3 rounded-xl border border-base-200">
                                    <div className="flex items-center gap-3">
                                        <input
                                            type="email"
                                            placeholder="correo@empresa.com"
                                            value={row.email}
                                            onChange={e => handleEmailChange(idx, 'email', e.target.value)}
                                            className={`input input-bordered input-sm flex-1 ${errors[`emails.${idx}.email`] ? 'input-error' : ''}`}
                                        />
                                        <label className="label cursor-pointer gap-2 text-xs">
                                            <input
                                                type="radio"
                                                name="email_principal"
                                                checked={row.es_principal}
                                                onChange={e => handleEmailChange(idx, 'es_principal', e.target.checked)}
                                                className="radio radio-xs radio-primary"
                                            />
                                            Principal
                                        </label>
                                        {data.emails.length > 1 && (
                                            <button type="button" onClick={() => removeEmailRow(idx)}
                                                    className="btn btn-xs btn-ghost text-error">
                                                <span className="icon-[lucide--trash-2] text-sm"></span>
                                            </button>
                                        )}
                                    </div>
                                    {errors[`emails.${idx}.email`] && (
                                        <span className="text-xs text-error">{errors[`emails.${idx}.email`]}</span>
                                    )}
                                </div>
                            ))}
                        </div>
                    )}

                    {activeTab === 'config' && (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="form-control bg-base-200/40 p-4 rounded-xl border border-base-200">
                                <label className="label cursor-pointer justify-between">
                                    <span className="label-text font-semibold text-xs">Mostrar en Directorio</span>
                                    <input
                                        type="checkbox"
                                        checked={data.mostrar_en_directorio}
                                        onChange={e => setData('mostrar_en_directorio', e.target.checked)}
                                        className="toggle toggle-primary toggle-sm"
                                    />
                                </label>
                            </div>

                            <div className="form-control bg-base-200/40 p-4 rounded-xl border border-base-200">
                                <label className="label cursor-pointer justify-between">
                                    <span className="label-text font-semibold text-xs">Mostrar en Cumpleaños</span>
                                    <input
                                        type="checkbox"
                                        checked={data.mostrar_en_cumpleanios}
                                        onChange={e => setData('mostrar_en_cumpleanios', e.target.checked)}
                                        className="toggle toggle-primary toggle-sm"
                                    />
                                </label>
                            </div>
                        </div>
                    )}
                </div>
            </div>

            <div className="flex items-center justify-end gap-3 bg-base-100 p-4 rounded-2xl border border-base-200">
                <Link href={cancelUrl} className="btn btn-sm btn-ghost">
                    Cancelar
                </Link>
                <button type="submit" disabled={processing} className="btn btn-sm btn-primary gap-2">
                    {processing && <span className="loading loading-spinner loading-xs"></span>}
                    {contacto ? 'Actualizar Contacto' : 'Guardar Contacto'}
                </button>
            </div>
        </form>
    );
}