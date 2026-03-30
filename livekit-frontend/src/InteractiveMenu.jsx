import React, { useState, useEffect } from 'react';

const MENU_DATA = {
    entrante: [
        { name: "Jamón Ibérico", price: 24, desc: "Corte a cuchillo con picos de Jerez" },
        { name: "Croquetas de Txangurro", price: 12, desc: "Crujientes con emulsión de ajo negro" },
        { name: "Ensalada de Burrata", price: 14, desc: "Con tomate rosa y pesto de pistacho" }
    ],
    principal: [
        { name: "Lomo de Bacalao", price: 22, desc: "A baja temperatura sobre pisto manchego" },
        { name: "Chuletón madurado", price: 45, desc: "Corte premium 1kg con patatas baby" },
        { name: "Arroz Meloso", price: 18, desc: "De marisco con carabinero" }
    ],
    postre: [
        { name: "Tarta de Queso", price: 8, desc: "Fluida con helado de frambuesa" },
        { name: "Torrija Caramelizada", price: 7, desc: "Con helado de vainilla Bourbon" }
    ]
};

export const InteractiveMenu = ({ currentCategory, highlightItem }) => {
    const categories = ['entrante', 'principal', 'postre'];
    
    return (
        <div className="glass-panel" style={{
            display: 'flex',
            flexDirection: 'column',
            gap: '16px',
            color: 'var(--text-primary)',
            padding: '24px',
            animation: 'fadeInLeft 0.5s ease-out',
            width: '380px',
            maxHeight: '60vh',
            overflowY: 'auto'
        }}>
            <h3 style={{
                fontFamily: '"Outfit", sans-serif',
                fontSize: '1.4rem',
                fontWeight: 700,
                color: 'var(--primary-main)',
                borderBottom: '1px solid rgba(255,255,255,0.1)',
                paddingBottom: '12px',
                marginBottom: '8px',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
            }}>
                <span style={{fontSize: '1.2rem'}}>📋</span> Carta Interactiva
            </h3>

            {categories.map(cat => (
                <div 
                    key={cat} 
                    style={{
                        padding: '16px',
                        background: currentCategory === cat ? 'rgba(139, 92, 246, 0.1)' : 'rgba(0,0,0,0.2)',
                        borderLeft: currentCategory === cat ? '4px solid var(--primary-main)' : '4px solid rgba(255,255,255,0.1)',
                        borderRadius: '0 12px 12px 0',
                        transition: 'all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275)'
                    }}
                >
                    <h4 style={{ 
                        textTransform: 'uppercase', 
                        letterSpacing: '2px', 
                        fontSize: '0.85rem',
                        fontWeight: 700,
                        color: currentCategory === cat ? 'var(--primary-main)' : 'rgba(255,255,255,0.4)',
                        marginBottom: '12px'
                    }}>
                        {cat}
                    </h4>
                    
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                        {MENU_DATA[cat].map(item => {
                            const isItemHighlighted = highlightItem && item.name.toLowerCase().includes(highlightItem.toLowerCase());
                            return (
                                <div key={item.name} style={{ 
                                    display: 'flex', 
                                    justifyContent: 'space-between', 
                                    alignItems: 'flex-start',
                                    padding: '8px',
                                    borderRadius: '8px',
                                    background: isItemHighlighted ? 'rgba(139, 92, 246, 0.2)' : 'transparent',
                                    border: isItemHighlighted ? '1px solid var(--primary-main)' : '1px solid transparent',
                                    transform: isItemHighlighted ? 'translateX(4px)' : 'none',
                                    transition: 'all 0.3s ease'
                                }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                        {isItemHighlighted && <span style={{ color: 'var(--primary-main)', animation: 'pulse 1.5s infinite' }}>►</span>}
                                        <div>
                                            <span style={{ 
                                                fontWeight: isItemHighlighted ? 700 : 500, 
                                                fontSize: '1rem', 
                                                color: isItemHighlighted || currentCategory === cat ? '#fff' : 'rgba(255,255,255,0.7)' 
                                            }}>
                                                {item.name}
                                            </span>
                                            <p style={{ fontSize: '0.8rem', color: 'rgba(255,255,255,0.5)', margin: '4px 0 0 0', lineHeight: 1.4 }}>
                                                {item.desc}
                                            </p>
                                        </div>
                                    </div>
                                    <span style={{ fontWeight: 600, color: isItemHighlighted ? '#fff' : 'var(--primary-light)', fontSize: '0.95rem' }}>
                                        {item.price}€
                                    </span>
                                </div>
                            );
                        })}
                    </div>
                </div>
            ))}
        </div>
    );
};
